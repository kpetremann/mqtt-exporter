"""Functional tests for MAX_METRICS limit."""

import prometheus_client
import pytest

from mqtt_exporter import main, settings
from mqtt_exporter.exceptions import MaximumMetricReached
from mqtt_exporter.main import PromMetricId


def _reset():
    """Reset prometheus registry and metrics."""
    # pylama: ignore=W0212
    collectors = list(prometheus_client.REGISTRY._collector_to_names.keys())
    for collector in collectors:
        prometheus_client.REGISTRY.unregister(collector)
    main.prom_metrics = {}


def test_max_metrics__unlimited(mocker):
    """Test that unlimited metrics (MAX_METRICS=0) allows any number of metrics."""
    _reset()
    original_max_metrics = settings.MAX_METRICS
    settings.MAX_METRICS = 0
    settings.MQTT_EXPOSE_CLIENT_ID = False
    settings.EXPOSE_LAST_SEEN = False

    try:
        main._create_msg_counter_metrics()
        main.prom_metrics = {}
        userdata = {"client_id": "test"}

        for i in range(10):
            msg = mocker.Mock()
            msg.topic = f"test/sensor{i}"
            msg.payload = f'{{"metric{i}": "1.0"}}'
            msg.properties = None
            main.expose_metrics(None, userdata, msg)

        assert len(main.prom_metrics) == 10

    finally:
        settings.MAX_METRICS = original_max_metrics


def test_max_metrics__within_limit(mocker):
    """Test that metrics can be created when within the limit."""
    _reset()
    original_max_metrics = settings.MAX_METRICS
    settings.MAX_METRICS = 5
    settings.MQTT_EXPOSE_CLIENT_ID = False
    settings.EXPOSE_LAST_SEEN = False

    try:
        main._create_msg_counter_metrics()
        main.prom_metrics = {}
        userdata = {"client_id": "test"}

        for i in range(3):
            msg = mocker.Mock()
            msg.topic = f"test/sensor{i}"
            msg.payload = f'{{"metric{i}": "{i}.0"}}'
            msg.properties = None
            main.expose_metrics(None, userdata, msg)

        # All 3 metrics should be created successfull
        assert len(main.prom_metrics) == 3
        assert PromMetricId("mqtt_metric0", ()) in main.prom_metrics
        assert PromMetricId("mqtt_metric1", ()) in main.prom_metrics
        assert PromMetricId("mqtt_metric2", ()) in main.prom_metrics

    finally:
        settings.MAX_METRICS = original_max_metrics


def test_max_metrics__exceeds_limit(mocker):
    """Test that new metrics cannot be created when limit is reached."""
    _reset()
    original_max_metrics = settings.MAX_METRICS
    settings.MAX_METRICS = 3
    settings.MQTT_EXPOSE_CLIENT_ID = False
    settings.EXPOSE_LAST_SEEN = False

    try:
        main._create_msg_counter_metrics()
        main.prom_metrics = {}
        userdata = {"client_id": "test"}

        for i in range(3):
            msg = mocker.Mock()
            msg.topic = f"test/sensor{i}"
            msg.payload = f'{{"metric{i}": "{i}.0"}}'
            msg.properties = None
            main.expose_metrics(None, userdata, msg)

        # Should have exactly 3 metrics
        assert len(main.prom_metrics) == 3

        msg = mocker.Mock()
        msg.topic = "test/sensor3"
        msg.payload = '{"metric3": "3.0"}'
        msg.properties = None
        main.expose_metrics(None, userdata, msg)

        assert len(main.prom_metrics) == 3
        assert PromMetricId("mqtt_metric3", ()) not in main.prom_metrics

    finally:
        settings.MAX_METRICS = original_max_metrics


def test_max_metrics__existing_metrics_can_be_updated(mocker):
    """Test that existing metrics can still be updated when limit is reached."""
    _reset()
    original_max_metrics = settings.MAX_METRICS
    settings.MAX_METRICS = 2
    settings.MQTT_EXPOSE_CLIENT_ID = False
    settings.EXPOSE_LAST_SEEN = False

    try:
        main._create_msg_counter_metrics()
        main.prom_metrics = {}
        userdata = {"client_id": "test"}

        msg = mocker.Mock()
        msg.topic = "test/sensor"
        msg.payload = '{"metric1": "1.0", "metric2": "2.0"}'
        msg.properties = None
        main.expose_metrics(None, userdata, msg)

        assert len(main.prom_metrics) == 2

        msg = mocker.Mock()
        msg.topic = "test/sensor"
        msg.payload = '{"metric1": "10.0", "metric2": "20.0"}'
        msg.properties = None
        main.expose_metrics(None, userdata, msg)

        assert len(main.prom_metrics) == 2

        metric1 = main.prom_metrics[PromMetricId("mqtt_metric1", ())].collect()
        assert metric1[0].samples[0].value == 10.0

        metric2 = main.prom_metrics[PromMetricId("mqtt_metric2", ())].collect()
        assert metric2[0].samples[0].value == 20.0

    finally:
        settings.MAX_METRICS = original_max_metrics


def test_max_metrics__direct_exception():
    """Test that _create_prometheus_metric raises MaximumMetricReached when limit exceeded."""
    _reset()
    original_max_metrics = settings.MAX_METRICS
    settings.MAX_METRICS = 2
    settings.MQTT_EXPOSE_CLIENT_ID = False
    settings.EXPOSE_LAST_SEEN = False

    try:
        main.prom_metrics = {}

        metric1 = PromMetricId("test_metric_1", ())
        metric2 = PromMetricId("test_metric_2", ())
        main._create_prometheus_metric(metric1, "test/topic1")
        main._create_prometheus_metric(metric2, "test/topic2")

        assert len(main.prom_metrics) == 2

        # Try to create a third metric - should raise exception
        metric3 = PromMetricId("test_metric_3", ())
        with pytest.raises(MaximumMetricReached) as exc_info:
            main._create_prometheus_metric(metric3, "test/topic3")

        assert "metric limit reached" in str(exc_info.value).lower()
        assert len(main.prom_metrics) == 2

    finally:
        settings.MAX_METRICS = original_max_metrics
