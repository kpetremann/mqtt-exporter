"""Exporter configuration."""

import os

PREFIX = os.getenv("PROMETHEUS_PREFIX", "mqtt_")
TOPIC_LABEL = os.getenv("TOPIC_LABEL", "topic")
TOPIC = os.getenv("MQTT_TOPIC", "#")
IGNORED_TOPICS = os.getenv("MQTT_IGNORED_TOPICS", "").split(",")
ZWAVE_TOPIC_PREFIX = os.getenv("ZWAVE_TOPIC_PREFIX", "zwave/")
ESPHOME_TOPIC_PREFIXES = os.getenv("ESPHOME_TOPIC_PREFIXES", "").split(",")
HUBITAT_TOPIC_PREFIXES = os.getenv("HUBITAT_TOPIC_PREFIXES", "hubitat/").split(",")
EXPOSE_LAST_SEEN = os.getenv("EXPOSE_LAST_SEEN", "False") == "True"
PARSE_MSG_PAYLOAD = os.getenv("PARSE_MSG_PAYLOAD", "True") == "True"
# 2000 is a very large number of metrics already, but should be high enough to avoid breaking users' setup
MAX_METRICS = int(os.getenv("MAX_METRICS", "2000"))


ZIGBEE2MQTT_AVAILABILITY = os.getenv("ZIGBEE2MQTT_AVAILABILITY", "False") == "True"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_MQTT_MESSAGE = os.getenv("LOG_MQTT_MESSAGE", "False") == "True"
MQTT_ADDRESS = os.getenv("MQTT_ADDRESS", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_V5_PROTOCOL = os.getenv("MQTT_V5_PROTOCOL", "False") == "True"
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "")
MQTT_EXPOSE_CLIENT_ID = os.getenv("MQTT_EXPOSE_CLIENT_ID", "False") == "True"
MQTT_ENABLE_TLS = os.getenv("MQTT_ENABLE_TLS", "False") == "True"
MQTT_TLS_NO_VERIFY = os.getenv("MQTT_TLS_NO_VERIFY", "False") == "True"
MQTT_TLS_CA_CERT = os.getenv("MQTT_TLS_CA_CERT")
MQTT_TLS_CLIENT_CERT = os.getenv("MQTT_TLS_CLIENT_CERT")
MQTT_TLS_CLIENT_KEY = os.getenv("MQTT_TLS_CLIENT_KEY")
PROMETHEUS_ADDRESS = os.getenv("PROMETHEUS_ADDRESS", "0.0.0.0")
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9000"))

KEEP_FULL_TOPIC = os.getenv("KEEP_FULL_TOPIC", "False") == "True"
