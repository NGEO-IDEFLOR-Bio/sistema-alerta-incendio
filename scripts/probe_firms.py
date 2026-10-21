"""Probe da API de área do NASA FIRMS.

Este script existe para **provar a coleta** de focos e registrar o schema **real**
observado na resposta — não a documentada. Ele faz **uma** chamada HTTP e grava:

- o payload cru em ``data/probes/<fonte>_<data>.csv`` (dados são gitignored);
- um relatório JSON de schema em ``data/probes/<fonte>_<data>_schema.json``;
- um resumo legível no stdout.

Não é a ingestão do sistema (F2) e não deve ser usado em produção.

Uso::

    export FIRMS_API_KEY=<MAP_KEY>          # Windows PowerShell: $env:FIRMS_API_KEY=...
    python scripts/probe_firms.py --date 2026-10-19

A chave gratuita é obtida em https://firms.modaps.eosdis.nasa.gov/api/map_key/
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov"
AREA_API_PATH = "/api/area/csv"
MAP_KEY_URL = "https://firms.modaps.eosdis.nasa.gov/api/map_key/"

DEFAULT_SOURCE = "VIIRS_NOAA20_NRT"
# Bounding box do estado do Pará (lon_min, lat_min, lon_max, lat_max).
# Origem: API de malhas do IBGE, estado 15 (Pará), municipalities,
# qualidade=minima — bbox calculado em 21/10/2026.
#   https://servicodados.ibge.gov.br/api/v3/malhas/estados/15
DEFAULT_BBOX = "-58.896,-9.842,-46.063,2.591"
DEFAULT_DAY_RANGE = 1

#: Nomes candidatos para os campos que importam, por sensor.
DATE_FIELDS = ("acq_date", "acquisition_date", "date")
TIME_FIELDS = ("acq_time", "acquisition_time", "time")
LAT_FIELDS = ("latitude", "lat")
LON_FIELDS = ("longitude", "lon")
SATELLITE_FIELDS = ("satellite",)
CONFIDENCE_FIELDS = ("confidence",)
FRP_FIELDS = ("frp",)

#: Textos que a API devolve com HTTP 200 quando a requisição é recusada.
ERROR_MARKERS = (
    "invalid map_key",
    "map key",
    "transaction limit",
    "exceed",
    "no data",
    "error",
)


class ProbeError(RuntimeError):
    """Falha explícita do probe (chave ausente, recusa da API, payload inválido)."""


@dataclass
class ProbeResult:
    """Resultado de uma chamada de área do FIRMS."""

    source: str
    date: str
    bbox: str
    day_range: int
    fetched_at_utc: str
    url: str
    columns: list[str]
    rows: list[dict[str, str]]
    raw_bytes: bytes
    report: dict[str, Any] = field(default_factory=dict)

    @property
    def n_records(self) -> int:
        return len(self.rows)


# --------------------------------------------------------------------------- #
# URL e transporte
# --------------------------------------------------------------------------- #
def map_key_from_env(env: dict[str, str] | None = None) -> str | None:
    """Devolve a MAP_KEY a partir do ambiente (``FIRMS_API_KEY`` ou ``FIRMS_MAP_KEY``)."""
    source = os.environ if env is None else env
    for name in ("FIRMS_API_KEY", "FIRMS_MAP_KEY"):
        value = (source.get(name) or "").strip()
        if value:
            return value
    return None


def build_url(
    map_key: str,
    source: str = DEFAULT_SOURCE,
    bbox: str = DEFAULT_BBOX,
    day_range: int = DEFAULT_DAY_RANGE,
    date: str | None = None,
    base: str = FIRMS_BASE,
) -> str:
    """Monta a URL da API de área.

    Formato verificado em https://firms.modaps.eosdis.nasa.gov/api/area/ :
    ``/api/area/csv/[MAP_KEY]/[SOURCE]/[AREA]/[DAY_RANGE]`` e, opcionalmente,
    ``/[DATE]`` (YYYY-MM-DD).
    """
    if not 1 <= day_range <= 5:
        raise ProbeError(f"day_range fora do permitido pela API (1..5): {day_range}")
    url = f"{base}{AREA_API_PATH}/{map_key}/{source}/{bbox}/{day_range}"
    if date:
        url = f"{url}/{date}"
    return url


def redact_key(url: str, map_key: str) -> str:
    """Remove a MAP_KEY da URL — ela viaja no path e não pode ir para log."""
    return url.replace(map_key, "***") if map_key else url


def detect_error(payload: bytes) -> str | None:
    """Detecta recusas que a API devolve com HTTP 200 e corpo em texto puro."""
    text = payload[:2048].decode("utf-8", "replace").strip().lower()
    if not text:
        return "resposta vazia"
    if text.startswith("<"):
        return "resposta HTML (provável redirecionamento para login Earthdata)"
    if "\n" in text or "," in text:
        return None
    if any(marker in text for marker in ERROR_MARKERS):
        return text.splitlines()[0][:300]
    return None


def fetch_area(url: str, timeout: int = 120) -> bytes:
    """Faz UMA requisição GET e devolve o payload cru."""
    request = urllib.request.Request(url, headers={"User-Agent": "ngeo-probe/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:  # pragma: no cover - depende da rede
        body = exc.read().decode("utf-8", "replace")[:300]
        raise ProbeError(f"HTTP {exc.code} da API FIRMS: {body}") from exc
    except urllib.error.URLError as exc:  # pragma: no cover - depende da rede
        raise ProbeError(f"Falha de rede na API FIRMS: {exc.reason}") from exc


# --------------------------------------------------------------------------- #
# Leitura e perfilagem do payload
# --------------------------------------------------------------------------- #
def parse_csv(payload: bytes) -> tuple[list[str], list[dict[str, str]]]:
    """Lê o CSV cru do FIRMS. Devolve (colunas, linhas) como texto cru."""
    if not payload.strip():
        raise ProbeError("payload vazio")
    text = payload.decode("utf-8-sig", "replace")
    reader = csv.DictReader(io.StringIO(text))
    columns = list(reader.fieldnames or [])
    if not columns:
        raise ProbeError("CSV sem cabeçalho")
    rows = [dict(row) for row in reader]
    return columns, rows


#: Mapeamento observado na API: o FIRMS entrega uma letra, não a palavra.
CONFIDENCE_BY_CODE = {"l": "low", "n": "nominal", "h": "high"}


def parse_acq_time(value: str) -> str:
    """Normaliza ``acq_time`` para ``HH:MM``.

    Observado na resposta real (21/10/2026): o campo **não tem zero à esquerda**
    — o valor ``353`` significa 03:53 e ``1633`` significa 16:33. Tratar como
    string de 4 dígitos quebra; tratar como inteiro e recompor é o correto.
    O horário é UTC.
    """
    raw = (value or "").strip()
    if not raw.isdigit():
        raise ProbeError(f"acq_time fora do formato esperado: {value!r}")
    if len(raw) > 4:
        raise ProbeError(f"acq_time com dígitos demais: {value!r}")
    padded = raw.zfill(4)
    if not (0 <= int(padded[:2]) <= 23 and 0 <= int(padded[2:]) <= 59):
        raise ProbeError(f"acq_time fora da faixa horária: {value!r}")
    return f"{padded[:2]}:{padded[2:]}"


def parse_acquisition_datetime(acq_date: str, acq_time: str) -> datetime:
    """Compõe o instante de aquisição (UTC) a partir de ``acq_date``/``acq_time``."""
    date_part = (acq_date or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_part):
        raise ProbeError(f"acq_date fora do formato esperado: {acq_date!r}")
    return datetime.strptime(f"{date_part} {parse_acq_time(acq_time)}", "%Y-%m-%d %H:%M").replace(
        tzinfo=UTC
    )


def normalize_confidence(value: str) -> str | None:
    """Converte a letra de confiança do FIRMS (``l``/``n``/``h``) em low/nominal/high."""
    code = (value or "").strip().lower()
    if not code:
        return None
    return CONFIDENCE_BY_CODE.get(code)


def _decimals(value: str) -> int | None:
    """Número de casas decimais de um número textual (None se não for número)."""
    if value is None or value == "":
        return None
    try:
        float(value)
    except ValueError:
        return None
    if "." not in value:
        return 0
    return len(value.split(".", 1)[1])


def _first(values: Iterable[str]) -> str | None:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _pick(columns: Sequence[str], candidates: Sequence[str]) -> str | None:
    lowered = {c.lower(): c for c in columns}
    for candidate in candidates:
        if candidate in lowered:
            return lowered[candidate]
    return None


def profile_columns(columns: Sequence[str], rows: Sequence[dict[str, str]]) -> list[dict[str, Any]]:
    """Perfil campo a campo: exemplos, cardinalidade, faixa numérica, decimais."""
    profile: list[dict[str, Any]] = []
    for column in columns:
        values = [str(row.get(column, "") or "") for row in rows]
        non_empty = [v for v in values if v != ""]
        numeric = []
        for value in non_empty:
            try:
                numeric.append(float(value))
            except ValueError:
                continue
        decimals = sorted({d for d in (_decimals(v) for v in non_empty) if d is not None})
        distinct = sorted(set(non_empty))
        entry: dict[str, Any] = {
            "name": column,
            "n_non_empty": len(non_empty),
            "n_distinct": len(distinct),
            "examples": distinct[:3],
            "all_empty": not non_empty,
        }
        if numeric and len(numeric) == len(non_empty):
            entry["numeric"] = True
            entry["min"] = min(numeric)
            entry["max"] = max(numeric)
            entry["decimals_observed"] = decimals
        else:
            entry["numeric"] = False
        profile.append(entry)
    return profile


def build_report(
    source: str,
    date: str,
    bbox: str,
    day_range: int,
    url: str,
    columns: Sequence[str],
    rows: Sequence[dict[str, str]],
) -> dict[str, Any]:
    """Monta o relatório de schema observado."""
    date_field = _pick(columns, DATE_FIELDS)
    time_field = _pick(columns, TIME_FIELDS)
    lat_field = _pick(columns, LAT_FIELDS)
    lon_field = _pick(columns, LON_FIELDS)
    sat_field = _pick(columns, SATELLITE_FIELDS)
    conf_field = _pick(columns, CONFIDENCE_FIELDS)
    frp_field = _pick(columns, FRP_FIELDS)

    def distinct_of(field_name: str | None, limit: int = 12) -> list[str]:
        if not field_name:
            return []
        return sorted({str(r.get(field_name, "") or "") for r in rows if r.get(field_name)})[:limit]

    def range_of(field_name: str | None) -> dict[str, float] | None:
        if not field_name:
            return None
        values = []
        for row in rows:
            try:
                values.append(float(str(row.get(field_name, ""))))
            except (TypeError, ValueError):
                continue
        if not values:
            return None
        return {"min": min(values), "max": max(values)}

    lat_range = range_of(lat_field)
    lon_range = range_of(lon_field)
    lat_decimals = sorted(
        {d for d in (_decimals(str(r.get(lat_field, ""))) for r in rows) if d is not None}  # type: ignore[arg-type]
    )
    lon_decimals = sorted(
        {d for d in (_decimals(str(r.get(lon_field, ""))) for r in rows) if d is not None}  # type: ignore[arg-type]
    )
    time_values = distinct_of(time_field, limit=8)
    time_decimals = sorted(
        {d for d in (_decimals(str(r.get(time_field, ""))) for r in rows) if d is not None}  # type: ignore[arg-type]
    )
    normalized_times = []
    time_parse_errors = []
    for value in time_values:
        try:
            normalized_times.append(parse_acq_time(value))
        except ProbeError as exc:
            time_parse_errors.append(f"{value}: {exc}")

    confidence_normalized = sorted(
        {
            norm
            for norm in (normalize_confidence(str(r.get(conf_field, "") or "")) for r in rows)
            if norm
        }
    )

    return {
        "observed_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "source": source,
        "date": date,
        "bbox_requested": bbox,
        "day_range": day_range,
        "url": url,
        "n_records": len(rows),
        "columns": list(columns),
        "column_profile": profile_columns(columns, rows),
        "fields": {
            "acquisition_date": {
                "column": date_field,
                "format": "YYYY-MM-DD" if date_field else None,
                "distinct_sample": distinct_of(date_field),
            },
            "acquisition_time": {
                "column": time_field,
                "format": "HHMM, inteiro, SEM zero à esquerda (ex.: '353' = 03:53 UTC)",
                "distinct_sample": time_values,
                "distinct_normalized": normalized_times,
                "decimals_observed": time_decimals,
                "parse_errors": time_parse_errors,
            },
            "latitude": {
                "column": lat_field,
                "min": lat_range["min"] if lat_range else None,
                "max": lat_range["max"] if lat_range else None,
                "decimals_observed": lat_decimals,
            },
            "longitude": {
                "column": lon_field,
                "min": lon_range["min"] if lon_range else None,
                "max": lon_range["max"] if lon_range else None,
                "decimals_observed": lon_decimals,
            },
            "satellite": {"column": sat_field, "distinct": distinct_of(sat_field)},
            "confidence": {
                "column": conf_field,
                "distinct": distinct_of(conf_field),
                "normalized": confidence_normalized,
                "note": "o FIRMS entrega a letra (l/n/h), não a palavra",
            },
            "frp": {
                "column": frp_field,
                "min": range_of(frp_field)["min"] if range_of(frp_field) else None,
                "max": range_of(frp_field)["max"] if range_of(frp_field) else None,
                "distinct_sample": distinct_of(frp_field),
            },
        },
    }


# --------------------------------------------------------------------------- #
# Execução
# --------------------------------------------------------------------------- #
def run_probe(
    map_key: str,
    source: str = DEFAULT_SOURCE,
    bbox: str = DEFAULT_BBOX,
    day_range: int = DEFAULT_DAY_RANGE,
    date: str | None = None,
    out_dir: Path | None = None,
    timeout: int = 120,
) -> ProbeResult:
    """Executa uma chamada real e devolve o resultado com o relatório de schema."""
    url = build_url(map_key, source=source, bbox=bbox, day_range=day_range, date=date)
    payload = fetch_area(url, timeout=timeout)

    error = detect_error(payload)
    if error:
        raise ProbeError(f"API FIRMS recusou a requisição: {error}")

    columns, rows = parse_csv(payload)
    safe_url = redact_key(url, map_key)
    report = build_report(source, date or "", bbox, day_range, safe_url, columns, rows)

    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = f"firms_{source}_{date or 'recent'}"
        (out_dir / f"{stem}.csv").write_bytes(payload)
        (out_dir / f"{stem}_schema.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return ProbeResult(
        source=source,
        date=date or "",
        bbox=bbox,
        day_range=day_range,
        fetched_at_utc=report["observed_at_utc"],
        url=safe_url,
        columns=columns,
        rows=rows,
        raw_bytes=payload,
        report=report,
    )


def format_summary(result: ProbeResult) -> str:
    """Resumo legível do schema observado."""
    fields = result.report["fields"]
    lines = [
        "=== FIRMS /api/area — schema REAL observado ===",
        f"fonte            : {result.source}",
        f"data             : {result.date or '(mais recente)'}",
        f"bbox             : {result.bbox}",
        f"registros        : {result.n_records}",
        f"colunas ({len(result.columns)}) : {', '.join(result.columns)}",
        "",
        f"latitude         : campo={fields['latitude']['column']} "
        f"min={fields['latitude']['min']} max={fields['latitude']['max']} "
        f"decimais={fields['latitude']['decimals_observed']}",
        f"longitude        : campo={fields['longitude']['column']} "
        f"min={fields['longitude']['min']} max={fields['longitude']['max']} "
        f"decimais={fields['longitude']['decimals_observed']}",
        f"data aquisição    : campo={fields['acquisition_date']['column']} "
        f"formato={fields['acquisition_date']['format']} "
        f"exemplos={fields['acquisition_date']['distinct_sample'][:3]}",
        f"hora aquisição    : campo={fields['acquisition_time']['column']} "
        f"formato={fields['acquisition_time']['format']} "
        f"normalizados={fields['acquisition_time']['distinct_normalized'][:4]}",
        f"satellite        : campo={fields['satellite']['column']} "
        f"valores={fields['satellite']['distinct']}",
        f"confidence       : campo={fields['confidence']['column']} "
        f"valores={fields['confidence']['distinct']} "
        f"normalizados={fields['confidence']['normalized']}",
        f"frp              : campo={fields['frp']['column']} "
        f"min={fields['frp']['min']} max={fields['frp']['max']} "
        f"exemplos={fields['frp']['distinct_sample'][:4]}",
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--bbox", default=DEFAULT_BBOX)
    parser.add_argument("--date", default=None, help="YYYY-MM-DD (default: mais recente)")
    parser.add_argument("--day-range", type=int, default=DEFAULT_DAY_RANGE)
    parser.add_argument(
        "--out",
        default="data/probes",
        help="diretório de saída (payload cru + relatório JSON). Default: data/probes",
    )
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args(argv)

    map_key = map_key_from_env()
    if not map_key:
        print(
            "ERRO: MAP_KEY ausente. Defina FIRMS_API_KEY no ambiente.\n"
            f"Chave gratuita: {MAP_KEY_URL}",
            file=sys.stderr,
        )
        return 2

    try:
        result = run_probe(
            map_key,
            source=args.source,
            bbox=args.bbox,
            day_range=args.day_range,
            date=args.date,
            out_dir=Path(args.out),
            timeout=args.timeout,
        )
    except ProbeError as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    print(format_summary(result))
    print(f"\npayload e relatório gravados em: {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
