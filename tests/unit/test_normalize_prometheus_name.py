"""Tests of Prometheus normalization metrics."""
from mqtt_exporter.main import _normalize_prometheus_metric_name


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
