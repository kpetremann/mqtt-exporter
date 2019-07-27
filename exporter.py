#!/usr/bin/env python3
"""MQTT exporter."""

import json
import logging
from prometheus_client import Gauge, start_http_server

import paho.mqtt.client as mqtt

METRIC = Gauge("mqtt_metric", "Metric generated from MQTT metric.", ["topic", "metric_name"])

logging.basicConfig()
LOG = logging.getLogger("mqtt-exporter")


def subscribe(client, userdata, flags, connection_result):  # pylint: disable=W0613
    """Subscribe to mqtt events (callback)."""
    client.subscribe("zigbee2mqtt/#")


def expose_metrics(client, userdata, msg):  # pylint: disable=W0613
    """Expose metrics to prometheus when a message has been published (callback)."""
    try:
        payload = json.loads(msg.payload)
        topic = msg.topic.replace("/", "_")
    except json.JSONDecodeError:
        LOG.warning('Failed to parse as JSON: "%s"', msg.payload)
        return

    for metric, value in payload.items():
        try:
            metric_value = float(value)
            METRIC.labels(topic=topic, metric_name=metric).set(metric_value)
        except ValueError:
            LOG.warning('Failed to convert: "%s=%s"', metric, value)


def main():
    """Start the exporter."""
    # start prometheus server
    start_http_server(9000)

    # define mqtt client
    client = mqtt.Client()
    client.on_connect = subscribe
    client.on_message = expose_metrics

    # start the connection and the loop
    client.connect("127.0.0.1", 1883, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()
