"""Functional tests for MQTT_METRICS_EXPIRE_SECONDS."""

from unittest.mock import patch

import prometheus_client
from prometheus_client import generate_latest

from mqtt_exporter import main, settings


def _reset():
    # pylama: ignore=W0212
    collectors = list(prometheus_client.REGISTRY._collector_to_names.keys())
    for collector in collectors:
        prometheus_client.REGISTRY.unregister(collector)
    main.prom_metrics = {}
    main.last_seen.clear()
    main.metric_refs.clear()


def test_metrics_ttl_removes_stale_series(mocker):
    """Stale payload gauges are removed after TTL; message counter remains."""
    _reset()
    saved_ttl = settings.MQTT_METRICS_EXPIRE_SECONDS
    saved_interval = settings.MQTT_METRICS_EXPIRE_INTERVAL_SECONDS
    settings.MQTT_METRICS_EXPIRE_SECONDS = 60
    settings.MQTT_METRICS_EXPIRE_INTERVAL_SECONDS = 30
    settings.MQTT_EXPOSE_CLIENT_ID = False
    settings.EXPOSE_LAST_SEEN = True
    settings.MQTT_V5_PROTOCOL = False
    settings.PARSE_MSG_PAYLOAD = True

    try:
        main._create_msg_counter_metrics()
        userdata = {"client_id": ""}
        msg = mocker.Mock()
        msg.topic = "zigbee2mqtt/garage"
        msg.payload = '{"temperature": "23.5", "humidity": "40.5"}'

        with patch.object(main.time, "time", return_value=1_000_000.0):
            main.expose_metrics(None, userdata, msg)

        text_before = generate_latest().decode()
        assert 'mqtt_temperature{topic="zigbee2mqtt_garage"}' in text_before
        assert 'mqtt_temperature_ts{topic="zigbee2mqtt_garage"}' in text_before
        assert "mqtt_message_total" in text_before

        with patch.object(main.time, "time", return_value=1_000_000.0 + 120.0):
            main.metrics_ttl_sweep_once()

        text_after = generate_latest().decode()
        # Empty metric families still emit HELP/TYPE lines; assert time series samples are gone.
        assert 'mqtt_temperature{topic="zigbee2mqtt_garage"}' not in text_after
        assert 'mqtt_temperature_ts{topic="zigbee2mqtt_garage"}' not in text_after
        assert 'mqtt_humidity{topic="zigbee2mqtt_garage"}' not in text_after
        assert "mqtt_message_total" in text_after
    finally:
        settings.MQTT_METRICS_EXPIRE_SECONDS = saved_ttl
        settings.MQTT_METRICS_EXPIRE_INTERVAL_SECONDS = saved_interval


def test_metrics_ttl_disabled_no_last_seen_updates(mocker):
    """When TTL is disabled, last_seen stays empty."""
    _reset()
    saved_ttl = settings.MQTT_METRICS_EXPIRE_SECONDS
    settings.MQTT_METRICS_EXPIRE_SECONDS = None
    settings.MQTT_EXPOSE_CLIENT_ID = False
    settings.MQTT_V5_PROTOCOL = False
    settings.PARSE_MSG_PAYLOAD = True

    try:
        main._create_msg_counter_metrics()
        userdata = {"client_id": ""}
        msg = mocker.Mock()
        msg.topic = "zigbee2mqtt/garage"
        msg.payload = '{"temperature": "23.5"}'
        main.expose_metrics(None, userdata, msg)
        assert main.last_seen == {}
        main.metrics_ttl_sweep_once()
        assert 'mqtt_temperature{topic="zigbee2mqtt_garage"}' in generate_latest().decode()
    finally:
        settings.MQTT_METRICS_EXPIRE_SECONDS = saved_ttl
