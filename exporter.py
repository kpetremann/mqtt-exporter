#!/usr/bin/env python3
"""MQTT exporter."""

import json
import logging
import os
import signal
import sys

import paho.mqtt.client as mqtt
from prometheus_client import Gauge, Counter, start_http_server

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
LOG = logging.getLogger("mqtt-exporter")
PREFIX = os.environ.get("PROMETHEUS_PREFIX", "mqtt_")
TOPIC_LABEL = os.environ.get("TOPIC_LABEL", "topic")
TOPIC = os.environ.get("MQTT_TOPIC", "#")
IGNORED_TOPICS = os.getenv("MQTT_IGNORED_TOPICS", "").split(",")

# global variable
prom_metrics = {}  # pylint: disable=C0103
prom_msg_counter = Counter(f"{PREFIX}message_total", "Counter of received messages", [TOPIC_LABEL])


def subscribe(client, userdata, flags, connection_result):  # pylint: disable=W0613
    """Subscribe to mqtt events (callback)."""
    LOG.info('listening to "%s"', TOPIC)
    client.subscribe(TOPIC)


def expose_metrics(client, userdata, msg):  # pylint: disable=W0613
    """Expose metrics to prometheus when a message has been published (callback)."""
    if msg.topic not in IGNORED_TOPICS:
        LOG.debug('Topic "%s" was ignored', msg.topic)
        return
    try:
        payload = json.loads(msg.payload)
        topic = msg.topic.replace("/", "_")
    except json.JSONDecodeError:
        LOG.debug('failed to parse as JSON: "%s"', msg.payload)
        return

    # we except a dict from zigbee metrics in MQTT
    if not isinstance(payload, dict):
        LOG.debug('unexpected payload format: "%s"', payload)
        return

    for metric, value in payload.items():
        # we only expose numeric values
        try:
            metric_value = float(value)
        except (ValueError, TypeError):
            LOG.debug("Failed to convert %s: %s", metric, value)
            continue

        # create metric if does not exist
        prom_metric_name = f"{PREFIX}{metric}"
        if not prom_metrics.get(prom_metric_name):
            prom_metrics[prom_metric_name] = Gauge(
                prom_metric_name, "metric generated from MQTT message.", [TOPIC_LABEL]
            )
            LOG.info("creating prometheus metric: %s", prom_metric_name)

        # expose the metric to prometheus
        prom_metrics[prom_metric_name].labels(**{TOPIC_LABEL: topic}).set(metric_value)
        LOG.debug("new value for %s: %s", prom_metric_name, metric_value)
    # Now inc a counter for the message count
    prom_msg_counter.labels(**{TOPIC_LABEL: topic}).inc()


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
    mqtt_port = int(os.environ.get("MQTT_PORT", "1883"))
    mqtt_keepalive = int(os.environ.get("MQTT_KEEPALIVE", "60"))
    mqtt_username = os.environ.get("MQTT_USERNAME")
    mqtt_password = os.environ.get("MQTT_PASSWORD")
    prom_port = int(os.environ.get("PROMETHEUS_PORT", "9000"))

    # start prometheus server
    start_http_server(prom_port)

    # define mqtt client
    client.on_connect = subscribe
    client.on_message = expose_metrics

    # start the connection and the loop
    if mqtt_username and mqtt_password:
        client.username_pw_set(mqtt_username, mqtt_password)
    client.connect(mqtt_address, mqtt_port, mqtt_keepalive)
    client.loop_forever()


if __name__ == "__main__":
    main()
