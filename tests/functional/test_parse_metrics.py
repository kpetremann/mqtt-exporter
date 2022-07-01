"""Functional tests of metrics parsing."""
from mqtt_exporter.main import _parse_metrics


def test_parse_metrics__nested_with_dash_in_metric_name():
    """Test metrics parsing when dash in metric name.

    seen with tasmota + multiple DS18B20 sensors.

    refers to test_parse_message__nested_with_dash_in_metric_name()
    """
    parsed_topic = "tele_balcony_SENSOR"
    parsed_payload = {
        "Time": "2022-07-01T21:21:17",
        "DS18B20-1": {"Id": "022EDB070007", "Temperature": 15.9},
        "DS18B20-2": {"Id": "0316A279C254", "Temperature": 6.9},
        "TempUnit": "C",
    }

    _parse_metrics(parsed_payload, parsed_topic, "dummy_client_id")
