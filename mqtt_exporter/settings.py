"""Exporter configuration."""
import os

PREFIX = os.getenv("PROMETHEUS_PREFIX", "mqtt_")
TOPIC_LABEL = os.getenv("TOPIC_LABEL", "topic")
TOPIC = os.getenv("MQTT_TOPIC", "#")
IGNORED_TOPICS = os.getenv("MQTT_IGNORED_TOPICS", "").split(",")

ZIGBEE2MQTT_AVAILABILITY = os.getenv("ZIGBEE2MQTT_AVAILABILITY", "False") == "True"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MQTT_ADDRESS = os.getenv("MQTT_ADDRESS", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", "60"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_V5_PROTOCOL = os.getenv("MQTT_V5_PROTOCOL", "False") == "True"
MQTT_EXPOSE_CLIENT_ID = os.getenv("MQTT_EXPOSE_CLIENT_ID", "False") == "True"
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9000"))
