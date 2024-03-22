"""Tests of Prometheus normalization metrics."""

import pytest

from mqtt_exporter.main import (
    _normalize_prometheus_metric_label_name,
    _normalize_prometheus_metric_name,
)


def test_normalize_prometheus_metric_name():
    """Test _normalize_prometheus_metric_name."""
    tests = {
        "1234invalid": ":1234invalid",
        "valid1234": "valid1234",
        "_this_is_valid": "_this_is_valid",
        "not_so_valid%_name": "not_so_valid_name",
    }

    for candidate, wanted in tests.items():
        assert _normalize_prometheus_metric_name(candidate) == wanted


@pytest.mark.parametrize(
    "candidate, wanted",
    [
        ("1234invalid", "_1234invalid"),
        ("valid1234", "valid1234"),
        ("_this_is_valid", "_this_is_valid"),
        ("not_so_valid%_name", "not_so_valid_name"),
        ("__using_reserved_prefix", "_using_reserved_prefix"),
        ("1_start_with_number", "_1_start_with_number"),
        ("%start_with_invalid_char", "start_with_invalid_char"),
        ("%__start_with_invalid_char", "_start_with_invalid_char"),
        ("_%_start_with_invalid_char", "_start_with_invalid_char"),
    ],
)
def test_normalize_prometheus_metric_label_name(candidate, wanted):
    """Test _normalize_prometheus_metric_label_name."""
    assert _normalize_prometheus_metric_label_name(candidate) == wanted
