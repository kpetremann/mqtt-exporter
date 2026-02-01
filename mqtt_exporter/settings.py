"""Exporter configuration."""

import logging
import os

LOG = logging.getLogger("mqtt-exporter")

PREFIX = os.getenv("PROMETHEUS_PREFIX", "mqtt_")
TOPIC_LABEL = os.getenv("TOPIC_LABEL", "topic")
TOPIC = os.getenv("MQTT_TOPIC", "#")
IGNORED_TOPICS = os.getenv("MQTT_IGNORED_TOPICS", "").split(",")
ZWAVE_TOPIC_PREFIX = os.getenv("ZWAVE_TOPIC_PREFIX", "zwave/")
ESPHOME_TOPIC_PREFIXES = os.getenv("ESPHOME_TOPIC_PREFIXES", "").split(",")
HUBITAT_TOPIC_PREFIXES = os.getenv("HUBITAT_TOPIC_PREFIXES", "hubitat/").split(",")
EXPOSE_LAST_SEEN = os.getenv("EXPOSE_LAST_SEEN", "False").lower() == "true"
PARSE_MSG_PAYLOAD = os.getenv("PARSE_MSG_PAYLOAD", "True").lower() == "true"
# 2000 is a very large number of metrics already, but should be high enough to avoid breaking users' setup
MAX_METRICS = int(os.getenv("MAX_METRICS", "2000"))


ZIGBEE2MQTT_AVAILABILITY = os.getenv("ZIGBEE2MQTT_AVAILABILITY", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_MQTT_MESSAGE = os.getenv("LOG_MQTT_MESSAGE", "False").lower() == "true"
MQTT_ADDRESS = os.getenv("MQTT_ADDRESS", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_PASSWORD_FILE = os.getenv("MQTT_PASSWORD_FILE")

if MQTT_PASSWORD_FILE:
    if MQTT_PASSWORD:
        raise ValueError("MQTT_PASSWORD_FILE is mutually exclusive with MQTT_PASSWORD")
    with open(MQTT_PASSWORD_FILE, "r") as f:
        MQTT_PASSWORD = f.read()

MQTT_V5_PROTOCOL = os.getenv("MQTT_V5_PROTOCOL", "False").lower() == "true"
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "")
MQTT_EXPOSE_CLIENT_ID = os.getenv("MQTT_EXPOSE_CLIENT_ID", "False").lower() == "true"
MQTT_ENABLE_TLS = os.getenv("MQTT_ENABLE_TLS", "False").lower() == "true"
MQTT_TLS_NO_VERIFY = os.getenv("MQTT_TLS_NO_VERIFY", "False").lower() == "true"
MQTT_TLS_CA_CERT = os.getenv("MQTT_TLS_CA_CERT")
MQTT_TLS_CLIENT_CERT = os.getenv("MQTT_TLS_CLIENT_CERT")
MQTT_TLS_CLIENT_KEY = os.getenv("MQTT_TLS_CLIENT_KEY")
PROMETHEUS_ADDRESS = os.getenv("PROMETHEUS_ADDRESS", "0.0.0.0")
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9000"))
PROMETHEUS_CERT = os.getenv("PROMETHEUS_CERT", None)
PROMETHEUS_CERT_KEY = os.getenv("PROMETHEUS_CERT_KEY", None)
PROMETHEUS_CA = os.getenv("PROMETHEUS_CA", None)
PROMETHEUS_CA_DIR = os.getenv("PROMETHEUS_CA_DIR", None)

KEEP_FULL_TOPIC = os.getenv("KEEP_FULL_TOPIC", "False").lower() == "true"

# State value mappings - can be extended via STATE_VALUES environment variable
# Format: "KEY1=VALUE1,KEY2=VALUE2" (e.g., "OPEN=1,CLOSED=0,LOCKED=1,UNLOCKED=0")
DEFAULT_STATE_VALUES = {
    "ON": 1,
    "OFF": 0,
    "TRUE": 1,
    "FALSE": 0,
    "ONLINE": 1,
    "OFFLINE": 0,
}

# Parse custom state values from environment variable
STATE_VALUES = DEFAULT_STATE_VALUES.copy()
custom_states = os.getenv("STATE_VALUES", "")
if custom_states:
    try:
        for pair in custom_states.split(","):
            if "=" in pair:
                key, value = pair.split("=", 1)
                STATE_VALUES[key.strip().upper()] = float(value.strip())
    except (ValueError, AttributeError) as e:
        # Log warning but continue with defaults
        LOG.warning("Failed to parse STATE_VALUES environment variable: %s", e)
