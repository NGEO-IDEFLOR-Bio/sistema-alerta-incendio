"""Testes do probe FIRMS.

Rodam **sem rede**: usam a fixture gravada a partir da resposta real de
21/10/2026 (`tests/fixtures/firms_viirs_noaa20_nrt_2026-10-19.csv`), um recorte
de 5 linhas da chamada de área do NASA FIRMS sobre o Pará.
"""

from __future__ import annotations

import json
from datetime import UTC
from pathlib import Path

import pytest

from scripts.probe_firms import (
    DEFAULT_BBOX,
    ProbeError,
    build_report,
    build_url,
    detect_error,
    map_key_from_env,
    normalize_confidence,
    parse_acq_time,
    parse_acquisition_datetime,
    parse_csv,
    profile_columns,
    redact_key,
)

FIXTURE = Path(__file__).parent / "fixtures" / "firms_viirs_noaa20_nrt_2026-10-19.csv"

EXPECTED_COLUMNS = [
    "latitude",
    "longitude",
    "bright_ti4",
    "scan",
    "track",
    "acq_date",
    "acq_time",
    "satellite",
    "instrument",
    "confidence",
    "version",
    "bright_ti5",
    "frp",
    "daynight",
]


@pytest.fixture(scope="module")
def payload() -> bytes:
    return FIXTURE.read_bytes()


@pytest.fixture(scope="module")
def parsed(payload: bytes) -> tuple[list[str], list[dict[str, str]]]:
    return parse_csv(payload)


def test_fixture_matches_real_schema(parsed: tuple[list[str], list[dict[str, str]]]) -> None:
    columns, rows = parsed
    assert columns == EXPECTED_COLUMNS
    assert len(rows) == 6


def test_coordinates_are_decimal_degrees(parsed: tuple[list[str], list[dict[str, str]]]) -> None:
    _, rows = parsed
    for row in rows:
        lat = float(row["latitude"])
        lon = float(row["longitude"])
        assert -90.0 <= lat <= 90.0
        assert -180.0 <= lon <= 180.0
        # O recorte pedido é o Pará; tudo tem de estar dentro da bbox.
        assert float(DEFAULT_BBOX.split(",")[0]) <= lon <= float(DEFAULT_BBOX.split(",")[2])
        assert float(DEFAULT_BBOX.split(",")[1]) <= lat <= float(DEFAULT_BBOX.split(",")[3])


def test_coordinate_precision_is_variable(parsed: tuple[list[str], list[dict[str, str]]]) -> None:
    """O campo de coordenada não tem precisão fixa — é o centro do pixel, não um GPS."""
    _, rows = parsed

    def decimals(field: str) -> set[int]:
        return {len(row[field].split(".")[1]) for row in rows}

    lat_decimals = decimals("latitude")
    lon_decimals = decimals("longitude")
    assert len(lat_decimals | lon_decimals) > 1, "esperado: precisão variável entre registros"
    assert all(1 <= d <= 6 for d in lat_decimals | lon_decimals)


def test_acq_time_is_hhmm_without_left_padding() -> None:
    assert parse_acq_time("353") == "03:53"
    assert parse_acq_time("1633") == "16:33"
    assert parse_acq_time("0007") == "00:07"


def test_acq_time_rejects_garbage() -> None:
    with pytest.raises(ProbeError):
        parse_acq_time("2530")
    with pytest.raises(ProbeError):
        parse_acq_time("ab")


def test_acquisition_datetime_is_utc(parsed: tuple[list[str], list[dict[str, str]]]) -> None:
    _, rows = parsed
    moment = parse_acquisition_datetime(rows[0]["acq_date"], rows[0]["acq_time"])
    assert moment.tzinfo is UTC
    assert moment.isoformat() == "2026-10-19T03:53:00+00:00"


def test_confidence_is_a_letter_not_a_word(parsed: tuple[list[str], list[dict[str, str]]]) -> None:
    _, rows = parsed
    assert {row["confidence"] for row in rows} <= {"l", "n", "h"}
    assert normalize_confidence("l") == "low"
    assert normalize_confidence("n") == "nominal"
    assert normalize_confidence("h") == "high"
    assert normalize_confidence("") is None


def test_viirs_has_ti4_ti5_and_no_brightness(
    parsed: tuple[list[str], list[dict[str, str]]],
) -> None:
    """O schema do VIIRS difere do MODIS: não existe 'brightness' nem 'bright_t31'."""
    columns, rows = parsed
    assert "brightness" not in columns
    assert "bright_t31" not in columns
    assert "bright_ti4" in columns and "bright_ti5" in columns
    for row in rows:
        assert 200.0 < float(row["bright_ti4"]) < 400.0
        assert 200.0 < float(row["bright_ti5"]) < 400.0


def test_frp_is_positive_megawatts(parsed: tuple[list[str], list[dict[str, str]]]) -> None:
    _, rows = parsed
    for row in rows:
        assert float(row["frp"]) > 0.0


def test_report_describes_observed_schema(parsed: tuple[list[str], list[dict[str, str]]]) -> None:
    columns, rows = parsed
    report = build_report(
        source="VIIRS_NOAA20_NRT",
        date="2026-10-19",
        bbox=DEFAULT_BBOX,
        day_range=1,
        url="https://firms.modaps.eosdis.nasa.gov/api/area/csv/***/VIIRS_NOAA20_NRT/x/1/2026-10-19",
        columns=columns,
        rows=rows,
    )
    assert report["n_records"] == 6
    assert report["columns"] == EXPECTED_COLUMNS
    fields = report["fields"]
    assert fields["latitude"]["column"] == "latitude"
    assert fields["latitude"]["min"] == pytest.approx(-9.40536)
    assert fields["acquisition_date"]["column"] == "acq_date"
    assert fields["acquisition_time"]["distinct_normalized"]
    assert fields["confidence"]["normalized"] == ["high", "low", "nominal"]
    assert fields["satellite"]["distinct"] == ["N20"]
    # relatório precisa ser serializável (vai para data/probes/*.json)
    json.dumps(report, ensure_ascii=False)


def test_profile_columns_flags_numeric_fields(
    parsed: tuple[list[str], list[dict[str, str]]],
) -> None:
    columns, rows = parsed
    profile = {entry["name"]: entry for entry in profile_columns(columns, rows)}
    assert profile["latitude"]["numeric"] is True
    assert profile["confidence"]["numeric"] is False
    assert profile["acq_date"]["all_empty"] is False


def test_detect_error_flags_refusals() -> None:
    assert detect_error(b"Invalid MAP_KEY.") is not None
    assert detect_error(b"") is not None
    assert detect_error(b"<html><body>login</body></html>") is not None
    assert detect_error(b"latitude,longitude\n-3.0,-47.0\n") is None


def test_build_url_matches_documented_format() -> None:
    url = build_url(
        "KEY", source="VIIRS_NOAA20_NRT", bbox="-1,-2,3,4", day_range=1, date="2026-10-19"
    )
    assert url == (
        "https://firms.modaps.eosdis.nasa.gov/api/area/csv/KEY/VIIRS_NOAA20_NRT/-1,-2,3,4/1/2026-10-19"
    )


def test_build_url_rejects_day_range_outside_api_limit() -> None:
    with pytest.raises(ProbeError):
        build_url("KEY", day_range=6)


def test_key_is_redacted_from_url() -> None:
    url = build_url("SEKRIT", bbox="-1,-2,3,4", date="2026-10-19")
    assert "SEKRIT" not in redact_key(url, "SEKRIT")


def test_map_key_from_env() -> None:
    assert map_key_from_env({"FIRMS_API_KEY": "abc"}) == "abc"
    assert map_key_from_env({"FIRMS_MAP_KEY": "def"}) == "def"
    assert map_key_from_env({}) is None
    assert map_key_from_env({"FIRMS_API_KEY": "  "}) is None
