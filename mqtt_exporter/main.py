#!/usr/bin/env python3
"""MQTT exporter."""

import argparse
import fnmatch
import json
import logging
import re
import signal
import ssl
import sys
import time
from collections import defaultdict
from dataclasses import dataclass

import paho.mqtt.client as mqtt
from prometheus_client import (
    REGISTRY,
    Counter,
    Gauge,
    generate_latest,
    start_http_server,
    validation,
)

from mqtt_exporter import settings
from mqtt_exporter.exceptions import MaximumMetricReached

logging.basicConfig(level=settings.LOG_LEVEL)
LOG = logging.getLogger("mqtt-exporter")

ZIGBEE2MQTT_AVAILABILITY_SUFFIX = "/availability"
STATE_VALUES = {
    "ON": 1,
    "OFF": 0,
    "TRUE": 1,
    "FALSE": 0,
    "ONLINE": 1,
    "OFFLINE": 0,
}


@dataclass(frozen=True)
class PromMetricId:
    name: str
    labels: tuple = ()


# global variables
metric_refs: dict[str, list[tuple]] = defaultdict(list)
prom_metrics: dict[PromMetricId, Gauge] = {}
prom_msg_counter = None


def _create_msg_counter_metrics():
    global prom_msg_counter  # noqa: PLW0603
    if settings.MQTT_EXPOSE_CLIENT_ID:
        prom_msg_counter = Counter(  # noqa: PLW0603
            f"{settings.PREFIX}message_total",
            "Counter of received messages",
            [settings.TOPIC_LABEL, "client_id"],
        )
    else:
        prom_msg_counter = Counter(  # noqa: PLW0603
            f"{settings.PREFIX}message_total",
            "Counter of received messages",
            [settings.TOPIC_LABEL],
        )


def subscribe(client, _, __, reason_code, properties):
    """Subscribe to mqtt events (callback)."""
    user_data = {"client_id": settings.MQTT_CLIENT_ID}
    if not settings.MQTT_CLIENT_ID and settings.MQTT_V5_PROTOCOL:
        user_data["client_id"] = properties.AssignedClientIdentifier

    client.user_data_set(user_data)

    for s in settings.TOPIC.split(","):
        LOG.info('subscribing to "%s"', s)
        client.subscribe(s)
    if reason_code != mqtt.CONNACK_ACCEPTED:
        LOG.error("MQTT %s", mqtt.connack_string(reason_code))


def _normalize_prometheus_metric_name(prom_metric_name):
    """Transform an invalid prometheus metric to a valid one.

    https://prometheus.io/docs/concepts/data_model/#metric-names-and-labels
    """
    if validation.METRIC_NAME_RE.match(prom_metric_name):
        return prom_metric_name

    # clean invalid characters
    prom_metric_name = re.sub(r"[^a-zA-Z0-9_:]", "", prom_metric_name)

    # ensure to start with valid character
    if not re.match(r"^[a-zA-Z_:]", prom_metric_name):
        prom_metric_name = ":" + prom_metric_name

    return prom_metric_name


def _normalize_prometheus_metric_label_name(prom_metric_label_name):
    """Transform an invalid prometheus metric to a valid one.

    https://prometheus.io/docs/concepts/data_model/#metric-names-and-labels
    """
    # clean invalid characters
    prom_metric_label_name = re.sub(r"[^a-zA-Z0-9_]", "", prom_metric_label_name)

    # ensure to start with valid character
    if not re.match(r"^[a-zA-Z_]", prom_metric_label_name):
        prom_metric_label_name = "_" + prom_metric_label_name
    if prom_metric_label_name.startswith("__"):
        prom_metric_label_name = prom_metric_label_name[1:]

    return prom_metric_label_name


def _create_prometheus_metric(prom_metric_id, original_topic):
    """Create Prometheus metric if does not exist."""
    if not prom_metrics.get(prom_metric_id):
        if settings.MAX_METRICS > 0 and len(prom_metrics) >= settings.MAX_METRICS:
            raise MaximumMetricReached(
                f"metric limit reached ({settings.MAX_METRICS}): cannot create new metric {prom_metric_id}"
            )

        labels = [settings.TOPIC_LABEL]
        if settings.MQTT_EXPOSE_CLIENT_ID:
            labels.append("client_id")
        labels.extend(prom_metric_id.labels)

        prom_metrics[prom_metric_id] = Gauge(
            prom_metric_id.name, "metric generated from MQTT message.", labels
        )
        metric_refs[original_topic].append((prom_metric_id, labels))

        if settings.EXPOSE_LAST_SEEN:
            ts_metric_id = PromMetricId(f"{prom_metric_id.name}_ts", prom_metric_id.labels)
            prom_metrics[ts_metric_id] = Gauge(
                ts_metric_id.name, "timestamp of metric generated from MQTT message.", labels
            )
            metric_refs[original_topic].append((ts_metric_id, labels))

        LOG.info("creating prometheus metric: %s", prom_metric_id)


def _add_prometheus_sample(
    topic, original_topic, prom_metric_id, metric_value, client_id, additional_labels
):
    if prom_metric_id not in prom_metrics:
        return

    labels = {settings.TOPIC_LABEL: topic}
    if settings.MQTT_EXPOSE_CLIENT_ID:
        labels["client_id"] = client_id
    labels.update(additional_labels)

    prom_metrics[prom_metric_id].labels(**labels).set(metric_value)
    if not (prom_metric_id, labels) not in metric_refs[original_topic]:
        metric_refs[original_topic].append((prom_metric_id, labels))

    if settings.EXPOSE_LAST_SEEN:
        ts_metric_id = PromMetricId(f"{prom_metric_id.name}_ts", prom_metric_id.labels)
        prom_metrics[ts_metric_id].labels(**labels).set(int(time.time()))
        if not (ts_metric_id, labels) not in metric_refs[original_topic]:
            metric_refs[original_topic].append((ts_metric_id, labels))

    LOG.debug("new value for %s: %s", prom_metric_id, metric_value)


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


def _parse_metrics(data, topic, original_topic, client_id, prefix="", labels=None):
    """Attempt to parse a set of metrics.

    Note when `data` contains nested metrics this function will be called recursively.
    """
    if labels is None:
        labels = {}
    label_keys = tuple(sorted(labels.keys()))

    for metric, value in data.items():
        # when value is a list recursively call _parse_metrics to handle these messages
        if isinstance(value, list):
            LOG.debug("parsing list %s: %s", metric, value)
            _parse_metrics(
                dict(enumerate(value)),
                topic,
                original_topic,
                client_id,
                f"{prefix}{metric}_",
                labels,
            )
            continue

        # when value is a dict recursively call _parse_metrics to handle these messages
        if isinstance(value, dict):
            LOG.debug("parsing dict %s: %s", metric, value)
            _parse_metrics(value, topic, original_topic, client_id, f"{prefix}{metric}_", labels)
            continue

        try:
            metric_value = _parse_metric(value)
        except ValueError as err:
            LOG.debug("Failed to convert %s: %s", metric, err)
            continue

        # create metric if does not exist
        prom_metric_name = (
            f"{settings.PREFIX}{prefix}{metric}".replace(".", "")
            .replace(" ", "_")
            .replace("-", "_")
            .replace("/", "_")
        )
        prom_metric_name = re.sub(r"\((.*?)\)", "", prom_metric_name)
        prom_metric_name = _normalize_prometheus_metric_name(prom_metric_name)
        prom_metric_id = PromMetricId(prom_metric_name, label_keys)
        try:
            _create_prometheus_metric(prom_metric_id, original_topic)
        except (ValueError, MaximumMetricReached) as error:
            LOG.error("unable to create prometheus metric '%s': %s", prom_metric_id, error)
            return

        # expose the sample to prometheus
        _add_prometheus_sample(
            topic, original_topic, prom_metric_id, metric_value, client_id, labels
        )


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
    payload_dict = {}

    # Shellies format
    try:
        if settings.KEEP_FULL_TOPIC:  # options instead of hardcoded length
            topic = "/".join(info[:-1]).lower()
        else:
            topic = f"{info[0]}/{info[1]}".lower()

        payload_dict = {info[-1]: payload}  # usually the last element is the type of sensor
    except IndexError:
        pass

    return topic, payload_dict


def _normalize_zwave2mqtt_format(topic, payload):
    """Normalize zwave2mqtt format.

    Example:
    zwave/BackRoom/Multisensor/sensor_multilevel/endpoint_0/Air_temperature
    zwave/Stereo/PowerStrip/status

    Only supports named topics or at least when endpoint_ is defined:
    <mqtt_prefix>/<?node_location>/<node_name>/<class_name>/<endpoint>/<propertyName>/<propertyKey>
    """
    if "node_info" in topic or "endpoint_" not in topic:
        return topic, {}

    if not isinstance(payload, dict) or "value" not in payload:
        return topic, {}

    info = topic.split("/")

    # the endpoint location permits to differentiate the properties from the sensor ID
    properties_index = [i for i, k in enumerate(info) if k.startswith("endpoint_")][0] + 1

    topic = "/".join(info[:properties_index]).lower()
    properties = "_".join(info[properties_index:])
    payload_dict = {properties.lower(): payload["value"]}

    return topic, payload_dict


def _normalize_esphome_format(topic, payload):
    """Normalize esphome format.

    Example:
    esphome/sensor/temperature/state

    Only supports default state_topic:
    <topic_prefix>/<component_type>/<component_name>/state
    """
    info = topic.split("/")

    topic = f"{info[0].lower()}/{info[1].lower()}"
    payload_dict = {info[-2]: payload}
    return topic, payload_dict


def _normalize_hubitat_format(topic, payload):
    """Normalize hubitat format.

    Example:
    hubitat/hub1/some room/temperature/value
    """
    info = topic.split("/")

    if len(info) < 3:
        return topic, payload

    topic = f"{info[0].lower()}_{info[1].lower()}_{info[2].lower()}"
    payload_dict = {info[-2]: payload}
    return topic, payload_dict


def _is_esphome_topic(topic):
    for prefix in settings.ESPHOME_TOPIC_PREFIXES:
        if prefix and topic.startswith(prefix):
            return True

    return False


def _is_hubitat_topic(topic):
    for prefix in settings.HUBITAT_TOPIC_PREFIXES:
        if prefix and topic.startswith(prefix):
            return True

    return False


def _parse_message(raw_topic, raw_payload):
    """Parse topic and payload to have exposable information."""
    # parse MQTT payload
    try:
        if not isinstance(raw_payload, str):
            raw_payload = raw_payload.decode(json.detect_encoding(raw_payload))
    except UnicodeDecodeError as err:
        LOG.debug('encountered undecodable payload: "%s" (%s)', raw_payload, err)
        return None, None

    if raw_payload in STATE_VALUES:
        payload = STATE_VALUES[raw_payload]
    else:
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError as err:
            LOG.debug('failed to parse payload as JSON: "%s" (%s)', raw_payload, err)
            return None, None

    if raw_topic.startswith(settings.ZWAVE_TOPIC_PREFIX):
        topic, payload = _normalize_zwave2mqtt_format(raw_topic, payload)
    elif _is_hubitat_topic(raw_topic):
        topic, payload = _normalize_hubitat_format(raw_topic, payload)
    elif _is_esphome_topic(raw_topic):
        topic, payload = _normalize_esphome_format(raw_topic, payload)
    elif not isinstance(payload, dict):
        topic, payload = _normalize_name_in_topic_msg(raw_topic, payload)
    else:
        topic = raw_topic

    # handle device availability (only support non-legacy mode)
    if settings.ZIGBEE2MQTT_AVAILABILITY:
        if topic.endswith(ZIGBEE2MQTT_AVAILABILITY_SUFFIX) and "state" in payload:
            # move availability suffix added by Zigbee2MQTT from topic to payload
            # the goal is to have this kind of metric:
            #   mqtt_zigbee_availability{sensor="zigbee2mqtt_garage"} = 1.0
            topic = topic[: -len(ZIGBEE2MQTT_AVAILABILITY_SUFFIX)]
            payload = {"zigbee_availability": payload["state"]}

    # parse MQTT topic
    try:
        # handle nested topic
        topic = topic.replace("/", "_")
    except UnicodeDecodeError:
        LOG.debug('encountered undecodable topic: "%s"', raw_topic)
        return None, None

    # handle unconverted payload
    if not isinstance(payload, dict):
        LOG.debug('failed to parse: topic "%s" payload "%s"', raw_topic, payload)
        return None, None

    return topic, payload


def _parse_properties(properties):
    """Convert MQTTv5 properties to a dict."""
    if not hasattr(properties, "UserProperty"):
        return {}

    return {
        _normalize_prometheus_metric_label_name(key): value
        for key, value in properties.UserProperty
    }


def _zigbee2mqtt_rename(msg):
    # Remove old metrics following renaming

    payload = json.loads(msg.payload)
    old_topic = f"zigbee2mqtt/{payload['data']['from']}"
    if old_topic not in metric_refs:
        return

    for sample in metric_refs[old_topic]:
        try:
            prom_metrics[sample[0]].remove(*sample[1].values())
        except KeyError:
            pass

    del metric_refs[old_topic]

    # Remove old availability metrics following renaming

    if not settings.ZIGBEE2MQTT_AVAILABILITY:
        return

    old_topic_availability = f"{old_topic}{ZIGBEE2MQTT_AVAILABILITY_SUFFIX}"
    if old_topic_availability not in metric_refs:
        return

    for sample in metric_refs[old_topic_availability]:
        try:
            prom_metrics[sample[0]].remove(*sample[1].values())
        except KeyError:
            pass

    del metric_refs[old_topic_availability]


def expose_metrics(_, userdata, msg):
    """Expose metrics to prometheus when a message has been published (callback)."""

    if msg.topic.startswith("zigbee2mqtt/") and msg.topic.endswith("/rename"):
        _zigbee2mqtt_rename(msg)
        return

    for ignore in settings.IGNORED_TOPICS:
        if fnmatch.fnmatch(msg.topic, ignore):
            LOG.debug('Topic "%s" was ignored by entry "%s"', msg.topic, ignore)
            return

    if settings.LOG_MQTT_MESSAGE:
        LOG.debug("New message from MQTT: %s - %s", msg.topic, msg.payload)

    topic, payload = _parse_message(msg.topic, msg.payload)

    if not topic or not payload:
        return

    if settings.MQTT_V5_PROTOCOL:
        additional_labels = _parse_properties(msg.properties)
    else:
        additional_labels = {}

    if settings.PARSE_MSG_PAYLOAD:
        _parse_metrics(payload, topic, msg.topic, userdata["client_id"], labels=additional_labels)

    # increment received message counter
    labels = {settings.TOPIC_LABEL: topic}
    if settings.MQTT_EXPOSE_CLIENT_ID:
        labels["client_id"] = userdata["client_id"]

    prom_msg_counter.labels(**labels).inc()


def run():
    """Start the exporter."""
    if settings.MQTT_V5_PROTOCOL:
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=settings.MQTT_CLIENT_ID,
            protocol=mqtt.MQTTv5,
        )
    else:
        # if MQTT version 5 is not requested, we let MQTT lib choose the protocol version
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=settings.MQTT_CLIENT_ID
        )

    client.enable_logger(LOG)

    if settings.MQTT_ENABLE_TLS:
        LOG.debug("Enabling TLS on MQTT client")
        ssl_context = ssl.create_default_context()

        # custom CA support
        if settings.MQTT_TLS_CA_CERT:
            LOG.debug("loading custom CA certificate")
            ssl_context.load_verify_locations(cafile=settings.MQTT_TLS_CA_CERT)
        else:
            ssl_context.load_default_certs()

        # mTLS settings
        if settings.MQTT_TLS_CLIENT_CERT and settings.MQTT_TLS_CLIENT_KEY:
            LOG.debug("[mTLS] loading client certificate and key")
            ssl_context.load_cert_chain(
                certfile=settings.MQTT_TLS_CLIENT_CERT, keyfile=settings.MQTT_TLS_CLIENT_KEY
            )

        if settings.MQTT_TLS_NO_VERIFY:
            LOG.debug("Not verifying MQTT certificate authority is trusted")
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        client.tls_set_context(ssl_context)

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

    _create_msg_counter_metrics()
    signal.signal(signal.SIGTERM, stop_request)
    signal.signal(signal.SIGINT, stop_request)

    # start prometheus server
    start_http_server(settings.PROMETHEUS_PORT, settings.PROMETHEUS_ADDRESS)

    # define mqtt client
    client.on_connect = subscribe
    client.on_message = expose_metrics

    # start the connection and the loop
    if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
        client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
    client.connect(settings.MQTT_ADDRESS, settings.MQTT_PORT, settings.MQTT_KEEPALIVE)
    client.loop_forever()


def main_mqtt_exporter():
    """Main function of mqtt exporter"""
    parser = argparse.ArgumentParser(
        prog="MQTT-exporter",
        description="Simple generic MQTT Prometheus exporter for IoT working out of the box.",
        epilog="https://github.com/kpetremann/mqtt-exporter",
    )
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        topic = input("topic: ")
        payload = input("payload: ")
        print()

        # clear registry
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            REGISTRY.unregister(collector)

        print("## Debug ##\n")
        original_topic = topic
        topic, payload = _parse_message(topic, payload)
        print(f"parsed to: {topic} {payload}")

        _parse_metrics(payload, topic, original_topic, "", labels=None)
        print("\n## Result ##\n")
        print(str(generate_latest().decode("utf-8")))
    else:
        run()


if __name__ == "__main__":
    main_mqtt_exporter()
