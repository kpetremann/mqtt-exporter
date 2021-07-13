#!/usr/bin/env python3
"""MQTT exporter."""

import json
import logging
import signal
import sys

import paho.mqtt.client as mqtt
from prometheus_client import Counter, Gauge, start_http_server

from mqtt_exporter import settings

logging.basicConfig(level=settings.LOG_LEVEL)
LOG = logging.getLogger("mqtt-exporter")

# global variable
prom_metrics = {}  # pylint: disable=C0103
prom_msg_counter = Counter(
    f"{settings.PREFIX}message_total", "Counter of received messages", [settings.TOPIC_LABEL]
)


def subscribe(client, userdata, flags, connection_result):  # pylint: disable=W0613
    """Subscribe to mqtt events (callback)."""
    LOG.info('listening to "%s"', settings.TOPIC)
    client.subscribe(settings.TOPIC)


def expose_metrics(client, userdata, msg):  # pylint: disable=W0613
    """Expose metrics to prometheus when a message has been published (callback)."""
    if msg.topic in settings.IGNORED_TOPICS:
        LOG.debug('Topic "%s" was ignored', msg.topic)
        return
    try:
        payload = json.loads(msg.payload)
        topic = msg.topic.replace("/", "_")
    except json.JSONDecodeError:
        LOG.debug('failed to parse as JSON: "%s"', msg.payload)
        return
    except UnicodeDecodeError:
        LOG.debug('encountered undecodable payload: "%s"', msg.payload)
        return

    # we expect a dict from zigbee metrics in MQTT
    if not isinstance(payload, dict):
        LOG.debug('unexpected payload format: "%s"', payload)
        return

    for metric, value in payload.items():
        if not isinstance(value, (int, float, str, bytes)):
            continue  # Value is not parsable
        # we only expose numeric values and ON/OFF as 1/0
        state_values = {"ON": 0, "OFF": 1}
        if str(value).upper() in state_values:
            metric_value = state_values[str(value).upper()]
        else:
            try:
                metric_value = float(value)
            except (ValueError, TypeError):
                LOG.debug("Failed to convert %s: %s", metric, value)
                continue

        # create metric if does not exist
        prom_metric_name = f"{settings.PREFIX}{metric}"
        if not prom_metrics.get(prom_metric_name):
            prom_metrics[prom_metric_name] = Gauge(
                prom_metric_name, "metric generated from MQTT message.", [settings.TOPIC_LABEL]
            )
            LOG.info("creating prometheus metric: %s", prom_metric_name)

        # expose the metric to prometheus
        prom_metrics[prom_metric_name].labels(**{settings.TOPIC_LABEL: topic}).set(metric_value)
        LOG.debug("new value for %s: %s", prom_metric_name, metric_value)

    # increment received message counter
    prom_msg_counter.labels(**{settings.TOPIC_LABEL: topic}).inc()


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

    # start prometheus server
    start_http_server(settings.PROMETHEUS_PORT)

    # define mqtt client
    client.on_connect = subscribe
    client.on_message = expose_metrics

    # start the connection and the loop
    if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
        client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
    client.connect(settings.MQTT_ADDRESS, settings.MQTT_PORT, settings.MQTT_KEEPALIVE)
    client.loop_forever()


if __name__ == "__main__":
    main()
