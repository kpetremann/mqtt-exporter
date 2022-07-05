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


def test__parse_message__generic_single_value_style():
    """Test message parsing when payload is a single value (same as Shelly but more custom).

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


def test_parse_message__nested_with_dash_in_metric_name():
    """Test message parsing when dash in metric name.

    seen with tasmota + multiple DS18B20 sensors.
    """
    topic = "tele/balcony/SENSOR"
    payload = '{ \
        "Time": "2022-07-01T21:21:17", \
        "DS18B20-1": { \
            "Id": "022EDB070007", \
            "Temperature": 15.9 \
        }, \
        "DS18B20-2": { \
            "Id": "0316A279C254", \
            "Temperature": 6.9 \
        }, \
        "TempUnit": "C" \
    }'

    parsed_topic, parsed_payload = _parse_message(topic, payload)

    assert parsed_topic == "tele_balcony_SENSOR"
    assert parsed_payload == {
        "Time": "2022-07-01T21:21:17",
        "DS18B20-1": {"Id": "022EDB070007", "Temperature": 15.9},
        "DS18B20-2": {"Id": "0316A279C254", "Temperature": 6.9},
        "TempUnit": "C",
    }


def test_parse_message__zwave_js():
    """Test parsing of ZWavejs2Mqtt message."""
    topic = "zwave/BackRoom/Multisensor/sensor_multilevel/endpoint_0/Air_temperature"
    payload = '{"time":1656470510619,"value":83.2}'

    parsed_topic, parsed_payload = _parse_message(topic, payload)
    assert parsed_topic == "zwave_backroom_multisensor_sensor_multilevel_endpoint_0"
    assert parsed_payload == {"air_temperature": 83.2}


def test_parse_message__zwave_js__payload_not_dict():
    """Test parsing of ZWavejs2Mqtt message."""
    topic = "zwave/BackRoom/Multisensor/sensor_multilevel/endpoint_0/Air_temperature"
    payload = "83.2"

    parsed_topic, parsed_payload = _parse_message(topic, payload)
    assert parsed_topic == "zwave_BackRoom_Multisensor_sensor_multilevel_endpoint_0_Air_temperature"
    assert parsed_payload == {}
