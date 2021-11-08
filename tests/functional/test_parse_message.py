"""Functional tests of MQTT message parsing."""
from mqtt_exporter.main import _parse_message


def test__parse_message__aqara_style():
    """Test message parsing with Aqara style.

    Same format for SONOFF sensors.
    """
    topic = "zigbee2mqtt/0x00157d00032b1234"
    payload = '{"temperature":26.24,"humidity":45.37}'

    parsed_topic, parsed_payload = _parse_message(topic, payload)

    assert parsed_topic == "zigbee2mqtt_0x00157d00032b1234"
    assert parsed_payload == {"temperature": 26.24, "humidity": 45.37}


def test__parse_message__shelly_style():
    """Test message parsing with shelly style."""
    topic = "shellies/room/sensor/temperature"
    payload = b"20.00"

    parsed_topic, parsed_payload = _parse_message(topic, payload)

    assert parsed_topic == "shellies_room"
    assert parsed_payload == {"temperature": 20.00}


def test__parse_message__tasmota_style():
    """Test message parsing for tasmota default style.

    This is similar to Shelly's style.
    """
    topic = "dht/livingroom/TEMPERATURE"
    payload = "20.0"

    parsed_topic, parsed_payload = _parse_message(topic, payload)

    assert parsed_topic == "dht_livingroom"
    assert parsed_payload == {"TEMPERATURE": 20.0}


def test_parse_message__nested():
    """Test message parsing when nested payload."""
    topic = "sensor/room"
    payload = '{ \
        "Time": "2021-10-03T11:05:21", \
        "ENERGY": { \
            "Total": 152.657, \
            "Yesterday": 1.758, \
            "Today": 0.178, \
            "Power": 143, \
            "ApparentPower": 184, \
            "ReactivePower": 117, \
            "Factor": 0.77, \
            "Voltage": 235, \
            "Current": 0.784 \
        } \
    }'

    parsed_topic, parsed_payload = _parse_message(topic, payload)

    assert parsed_topic == "sensor_room"
    assert parsed_payload == {
        "Time": "2021-10-03T11:05:21",
        "ENERGY": {
            "Total": 152.657,
            "Yesterday": 1.758,
            "Today": 0.178,
            "Power": 143,
            "ApparentPower": 184,
            "ReactivePower": 117,
            "Factor": 0.77,
            "Voltage": 235,
            "Current": 0.784,
        },
    }
