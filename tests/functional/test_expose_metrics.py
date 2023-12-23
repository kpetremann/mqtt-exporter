"""Functional tests of MQTT metrics."""

import prometheus_client
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties

from mqtt_exporter import main, settings
from mqtt_exporter.main import PromMetricId


def _reset():
    # pylama: ignore=W0212
    collectors = list(prometheus_client.REGISTRY._collector_to_names.keys())
    for collector in collectors:
        prometheus_client.REGISTRY.unregister(collector)


def _exec(client_id, mocker, added_labels):
    _reset()
    settings.MQTT_CLIENT_ID = client_id
    main._create_msg_counter_metrics()
    main.prom_metrics = {}
    userdata = {"client_id": client_id}
    msg = mocker.Mock()
    msg.topic = "zigbee2mqtt/garage"
    msg.payload = '{"temperature°C": "23.5", "humidity": "40.5"}'
    if added_labels:
        msg.properties = Properties(PacketTypes.PUBLISH)
        msg.properties.UserProperty = [
            ("label_key", "label_value"),
            ("Weird#Label Key!", "Weird Label Value"),
        ]
        expected_label_keys = ("WeirdLabelKey", "label_key")
    else:
        expected_label_keys = ()
    main.expose_metrics(None, userdata, msg)

    temperatures = main.prom_metrics[
        PromMetricId("mqtt_temperatureC", expected_label_keys)
    ].collect()
    humidity = main.prom_metrics[PromMetricId("mqtt_humidity", expected_label_keys)].collect()

    return temperatures, humidity


def test_expose_metrics__default(mocker):
    """Tests with no client ID, client ID not exposed."""
    settings.MQTT_EXPOSE_CLIENT_ID = False
    temperatures, humidity = _exec("", mocker, False)

    assert len(temperatures) == 1
    assert len(temperatures[0].samples) == 1
    assert temperatures[0].samples[0].value == 23.5
    assert temperatures[0].samples[0].labels == {"topic": "zigbee2mqtt_garage"}

    assert len(humidity) == 1
    assert len(humidity[0].samples) == 1
    assert humidity[0].samples[0].value == 40.5
    assert humidity[0].samples[0].labels == {"topic": "zigbee2mqtt_garage"}


def test_expose_metrics__default_client_set_exposed(mocker):
    """Tests with client ID, client ID exposed."""
    settings.MQTT_EXPOSE_CLIENT_ID = True
    temperatures, humidity = _exec("clienttestid", mocker, False)

    assert len(temperatures) == 1
    assert len(temperatures[0].samples) == 1
    assert temperatures[0].samples[0].value == 23.5
    assert temperatures[0].samples[0].labels == {
        "client_id": "clienttestid",
        "topic": "zigbee2mqtt_garage",
    }

    assert len(humidity) == 1
    assert len(humidity[0].samples) == 1
    assert humidity[0].samples[0].value == 40.5
    assert humidity[0].samples[0].labels == {
        "client_id": "clienttestid",
        "topic": "zigbee2mqtt_garage",
    }


def test_expose_metrics__labels_from_user_properties(mocker):
    """Test that labels in UserProperty are added to metrics."""
    settings.MQTT_EXPOSE_CLIENT_ID = False
    settings.MQTT_V5_PROTOCOL = True
    temperatures, humidity = _exec("clienttestid", mocker, True)

    expected_labels = {
        "topic": "zigbee2mqtt_garage",
        "label_key": "label_value",
        "WeirdLabelKey": "Weird Label Value",
    }

    assert len(temperatures) == 1
    assert temperatures[0].samples[0].labels == expected_labels

    assert len(humidity) == 1
    assert humidity[0].samples[0].labels == expected_labels
