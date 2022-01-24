#!/usr/bin/env python3
"""MQTT exporter."""

import fnmatch
import json
import logging
import re
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
    "TRUE": 1,
    "FALSE": 0,
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


def _parse_metrics(data, topic, prefix=""):
    """Attempt to parse a set of metrics.

    Note when `data` contains nested metrics this function will be called recursivley.
    """
    for metric, value in data.items():
        # when value is a dict recursivley call _parse_metrics to handle these messages
        if isinstance(value, dict):
            LOG.debug("parsing dict %s: %s", metric, value)
            _parse_metrics(value, topic, f"{prefix}{metric}_")
            continue

        try:
            metric_value = _parse_metric(value)
        except ValueError as err:
            LOG.debug("Failed to convert %s: %s", metric, err)
            continue

        # create metric if does not exist
        prom_metric_name = f"{settings.PREFIX}{prefix}{metric}".replace(".", "").replace(" ", "_")
        prom_metric_name = re.sub(r"\((.*?)\)", "", prom_metric_name)
        if not prom_metrics.get(prom_metric_name):
            prom_metrics[prom_metric_name] = Gauge(
                prom_metric_name, "metric generated from MQTT message.", [settings.TOPIC_LABEL]
            )
            LOG.info("creating prometheus metric: %s", prom_metric_name)

        # expose the metric to prometheus
        prom_metrics[prom_metric_name].labels(**{settings.TOPIC_LABEL: topic}).set(metric_value)
        LOG.debug("new value for %s: %s", prom_metric_name, metric_value)


def _parse_metric(data):
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


def _normalize_name_in_topic_msg(topic, payload):
    """Normalize message to classic topic payload format.

    Used when payload is containing only the value, and the sensor metric name is in the topic.

    Used for:
    - Shelly sensors
    - Custom integration with single value

    Warning: only support when the last item in the topic is the actual metric name

    Example:
    Shelly integrated topic and payload differently than usually (Aqara)
    * topic: shellies/room/sensor/temperature
    * payload: 20.00
    """
    info = topic.split("/")
    try:
        topic = f"{info[0]}/{info[1]}".lower()
        payload_dict = {info[-1]: payload}  # usually the last element is the type of sensor
    except IndexError:
        pass

    return topic, payload_dict


def _parse_message(raw_topic, raw_payload):
    """Parse topic and payload to have exposable information."""
    # parse MQTT payload
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError:
        LOG.debug('failed to parse payload as JSON: "%s"', raw_payload)
        return None, None
    except UnicodeDecodeError:
        LOG.debug('encountered undecodable payload: "%s"', raw_payload)
        return None, None

    if not isinstance(payload, dict):
        topic, payload = _normalize_name_in_topic_msg(raw_topic, payload)
    else:
        topic = raw_topic

    # parse MQTT payload
    try:
        topic = topic.replace("/", "_")
    except UnicodeDecodeError:
        LOG.debug('encountered undecodable topic: "%s"', raw_topic)
        return None, None

    # handle not converted payload
    if not isinstance(payload, dict):
        LOG.debug('failed to parse: topic "%s" payload "%s"', raw_topic, payload)
        return None, None

    return topic, payload


def expose_metrics(client, userdata, msg):  # pylint: disable=W0613
    """Expose metrics to prometheus when a message has been published (callback)."""
    for ignore in settings.IGNORED_TOPICS:
        if fnmatch.fnmatch(msg.topic, ignore):
            LOG.debug('Topic "%s" was ignored by entry "%s"', msg.topic, ignore)
            return

    topic, payload = _parse_message(msg.topic, msg.payload)

    if not topic or not payload:
        return

    _parse_metrics(payload, topic)

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
