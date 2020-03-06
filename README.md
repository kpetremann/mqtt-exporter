![build](https://travis-ci.com/kpetremann/mqtt-exporter.svg?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/b1ca990b576342a48d771d472e64bc24)](https://www.codacy.com/app/kpetremann/mqtt-exporter?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=kpetremann/mqtt-exporter&amp;utm_campaign=Badge_Grade)
[![Maintainability](https://api.codeclimate.com/v1/badges/635c98a1b4701d1ab4cf/maintainability)](https://codeclimate.com/github/kpetremann/mqtt-exporter/maintainability)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# MQTT-exporter

## Description

Simple and generic Prometheus exporter for MQTT.
Tested with Mosquitto MQTT and Xiaomi sensors.

It exposes metrics from MQTT message out of the box (you just need to specify the target if not on localhost).

MQTT-exporter expects a topic and a JSON payload.

### Example
```
topic 'zigbee2mqtt/0x00157d00032b1234', payload '{"temperature":26.24,"humidity":45.37}'
```
will be converted as:
```
temperature{topic="zigbee2mqtt_0x00157d00032b1234"} 25.24
humidity{topic="zigbee2mqtt_0x00157d00032b1234"} 45.37
```

### Configuration

Parameters are passed using environment variables.

The list of parameters are:
-   `LOG_LEVEL`: Logging level (default: INFO)
-   `MQTT_ADDRESS`: IP or hostname of MQTT broker (default: 127.0.0.1)
-   `MQTT_PORT`: TCP port of MQTT broker (default: 1883)
-   `MQTT_KEEPALIVE`: Keep alive interval to maintain connection with MQTT broker (default: 60)
-   `MQTT_USERNAME`: Username which should be used to authenticate against the MQTT broker (default: None)
-   `MQTT_PASSWORD`: Password which should be used to authenticate against the MQTT broker (default: None)
-   `PROMETHEUS_PORT`: HTTP server PORT to expose Prometheus metrics (default: 9000) 
-   `PROMETHEUS_PREFIX`: Prefix added to the metric name, example: mqtt_temperature (default: mqtt_)
-   `TOPIC_LABEL`: Define the Prometheus label for the topic, example temperature{topic="device1"} (default: topic)

### Deployment

#### Using Docker

```shell
docker run -it -p 9000:9000 -e "MQTT_ADDRESS=192.168.0.1" kpetrem/mqtt-exporter
```

#### Using Docker Compose

```yaml
version: "3"
services:
  mqtt-exporter:
    image: kpetrem/mqtt-exporter
    ports:
      - 9000:9000
    environment:
      - MQTT_ADDRESS=192.168.0.1
```

#### Using Python

```
pip install -r requirements.txt
MQTT_ADDRESS=192.168.0.1 python exporter.py
```
