#!/usr/bin/env python3
"""MQTT exporter."""

import json
import logging
import os
import signal
import sys

import paho.mqtt.client as mqtt
from prometheus_client import Gauge, start_http_server

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
LOG = logging.getLogger("mqtt-exporter")
PREFIX = os.environ.get("PROMETHEUS_PREFIX", "mqtt_")

# global variable
prom_metrics = {}  # pylint: disable=C0103


def subscribe(client, userdata, flags, connection_result):  # pylint: disable=W0613
    """Subscribe to mqtt events (callback)."""
    client.subscribe("zigbee2mqtt/#")


def expose_metrics(client, userdata, msg):  # pylint: disable=W0613
    """Expose metrics to prometheus when a message has been published (callback)."""
    try:
        payload = json.loads(msg.payload)
        topic = msg.topic.replace("/", "_")
    except json.JSONDecodeError:
        LOG.warning('failed to parse as JSON: "%s"', msg.payload)
        return

    topic_label = os.environ.get("TOPIC_LABEL", "topic")
    for metric, value in payload.items():
        # we only expose numeric values
        try:
            metric_value = float(value)
        except ValueError:
            LOG.warning("Failed to convert %s: %s", metric, value)
            continue

        # create metric if does not exist
        prom_metric_name = f"{PREFIX}{metric}"
        if not prom_metrics.get(prom_metric_name):
            prom_metrics[prom_metric_name] = Gauge(
                prom_metric_name, "metric generated from MQTT message.", [topic_label]
            )
            LOG.info("creating prometheus metric: %s", prom_metric_name)

        # expose the metric to prometheus
        prom_metrics[prom_metric_name].labels(**{topic_label: topic}).set(metric_value)
        LOG.debug("new value for %s: %s", prom_metric_name, metric_value)


def main():
    """Start the exporter."""
    client = mqtt.Client()

    def stop_request(signum, frame):
        """Stop handler for SIGTERM and SIGINT.

        Keyword arguments:
        signum -- signal number
        frame -- None or a frame object. Represents execution frames
        """
        LOG.warning("Stopping MQTT exporter")
        LOG.debug("SIGNAL: %s, FRAME: %s", signum, frame)
        client.disconnect()
        sys.exit(0)

    signal.signal(signal.SIGTERM, stop_request)
    signal.signal(signal.SIGINT, stop_request)

    # get parameters from environment
    mqtt_address = os.environ.get("MQTT_ADDRESS", "127.0.0.1")
    mqtt_port = os.environ.get("MQTT_PORT", 1883)
    mqtt_keepalive = os.environ.get("MQTT_KEEPALIVE", 60)
    mqtt_username = os.environ.get("MQTT_USERNAME")
    mqtt_password = os.environ.get("MQTT_PASSWORD")

    # start prometheus server
    start_http_server(os.environ.get("PROMETHEUS_PORT", 9000))

    # define mqtt client
    client.on_connect = subscribe
    client.on_message = expose_metrics

    # start the connection and the loop
    if mqtt_username and mqtt_password:
        client.username_pw_set(mqtt_username, mqtt_password)
    client.connect(mqtt_address, int(mqtt_port), mqtt_keepalive)
    client.loop_forever()


if __name__ == "__main__":
    main()
