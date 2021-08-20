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

STATE_VALUES = {
    "ON": 1,
    "OFF": 0,
}

# global variable
prom_metrics = {}  # pylint: disable=C0103
prom_msg_counter = Counter(
    f"{settings.PREFIX}message_total", "Counter of received messages", [settings.TOPIC_LABEL]
)


def subscribe(client, userdata, flags, connection_result):  # pylint: disable=W0613
    """Subscribe to mqtt events (callback)."""
    LOG.info('listening to "%s"', settings.TOPIC)
    client.subscribe(settings.TOPIC)


def parse_metrics(data):
    """Attempt to parse the value and extract a number out of it.

    Note that `data` is untrusted input at this point.

    Raise ValueError is the data can't be parsed.
    """
    if isinstance(data, (int, float)):
        return data
    if isinstance(data, bytes):
        data = data.decode()
    if isinstance(data, str):
        data = data.upper()
        # Handling of switch data where their state is reported as ON/OFF
        if data in STATE_VALUES:
            return STATE_VALUES[data]
        # Last ditch effort, we got a string, let's try to cast it
        return float(data)
    # We were not able to extract anything, let's bubble it up.
    raise ValueError(f"Can't parse '{data}' to a number.")


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
        try:
            metric_value = parse_metrics(value)
        except ValueError as err:
            LOG.debug("Failed to convert %s: %s", metric, err)
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
