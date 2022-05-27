![build](https://travis-ci.com/kpetremann/mqtt-exporter.svg?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/b1ca990b576342a48d771d472e64bc24)](https://www.codacy.com/app/kpetremann/mqtt-exporter?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=kpetremann/mqtt-exporter&amp;utm_campaign=Badge_Grade)
[![Maintainability](https://api.codeclimate.com/v1/badges/635c98a1b4701d1ab4cf/maintainability)](https://codeclimate.com/github/kpetremann/mqtt-exporter/maintainability)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![Build and publish docker images](https://github.com/kpetremann/mqtt-exporter/workflows/Build%20and%20publish%20docker%20images%20(all%20platforms)/badge.svg)](https://hub.docker.com/r/kpetrem/mqtt-exporter)

# MQTT-exporter

## Description

Simple and generic Prometheus exporter for MQTT.
Tested with Mosquitto MQTT and Xiaomi sensors.

It exposes metrics from MQTT message out of the box (you just need to specify the target if not on localhost).

MQTT-exporter expects a topic and a flat JSON payload, the value must be numeric values.

It also provides message counters for each MQTT topic (since PR #5):
```
mqtt_message_total{instance="mqtt-exporter:9000", job="mqtt-exporter", topic="zigbee2mqtt_0x00157d00032b1234"} 10
```

### Tested devices

Note: This exporter aims to be as generic as possible. If the sensor you use is using the following format, it will work:
```
topic '<prefix>/<name>', payload '{"temperature":26.24,"humidity":45.37}'
```

Also, the Shelly format is supported:
```
topic '<prefix>/<name>/sensor/temperature' '20.00'
```

The exporter is tested with:
  * Aqara/Xiaomi sensors (WSDCGQ11LM and VOCKQJK11LM)
  * SONOFF sensors (SNZB-02)
  * Shelly sensors (H&T wifi)

### Metrics conversion example
```
topic 'zigbee2mqtt/0x00157d00032b1234', payload '{"temperature":26.24,"humidity":45.37}'
```
will be converted as:
```
mqtt_temperature{topic="zigbee2mqtt_0x00157d00032b1234"} 25.24
mqtt_humidity{topic="zigbee2mqtt_0x00157d00032b1234"} 45.37
```

### Zigbee2MQTT device availability support

**Note: Supports only non-legacy mode** - see [Device availability advanced](https://www.zigbee2mqtt.io/guide/configuration/device-availability.html#availability-advanced-configuration)

When exposing device availability, Zigbee2MQTT add /availability suffix in the topic. So we end up with inconsistent metrics:

```
mqtt_state{topic="zigbee2mqtt_garage_availability"} 1.0
mqtt_temperature{topic="zigbee2mqtt_garage"} 1.0
```

To avoid having different topic for the same device, the exporter has a normalization feature disabled by default.
It can be enabled by setting ZIGBEE2MQTT_AVAILABILITY varenv to "True".

I will remove the suffix from the topic, and change the metric name accordingly:

```
mqtt_zigbee_availability{topic="zigbee2mqtt_garage"} 1.0
mqtt_temperature{topic="zigbee2mqtt_garage"} 1.0
```

Note: the metric name mqtt_state  is not kept to reduce collision risks as it is too common.

### Configuration

Parameters are passed using environment variables.

The list of parameters are:
  * `LOG_LEVEL`: Logging level (default: INFO)
  * `MQTT_IGNORED_TOPICS`: Comma-separated lists of topics to ignore. Accepts wildcards. (default: None)
  * `MQTT_ADDRESS`: IP or hostname of MQTT broker (default: 127.0.0.1)
  * `MQTT_PORT`: TCP port of MQTT broker (default: 1883)
  * `MQTT_TOPIC`: Topic path to subscribe to (default: #)
  * `MQTT_KEEPALIVE`: Keep alive interval to maintain connection with MQTT broker (default: 60)
  * `MQTT_USERNAME`: Username which should be used to authenticate against the MQTT broker (default: None)
  * `MQTT_PASSWORD`: Password which should be used to authenticate against the MQTT broker (default: None)
  * `MQTT_V5_PROTOCOL`: Force to use MQTT protocol v5 instead of 3.1.1
  * `MQTT_CLIENT_ID`: Set client ID manually for MQTT connection
  * `MQTT_EXPOSE_CLIENT_ID`: Expose the client ID as a label in Prometheus metrics
  * `PROMETHEUS_PORT`: HTTP server PORT to expose Prometheus metrics (default: 9000)
  * `PROMETHEUS_PREFIX`: Prefix added to the metric name, example: mqtt_temperature (default: mqtt_)
  * `TOPIC_LABEL`: Define the Prometheus label for the topic, example temperature{topic="device1"} (default: topic)
  * `ZIGBEE2MQTT_AVAILABILITY`: Normalize sensor name for device availability metric added by Zigbee2MQTT (default: False)

### Deployment

#### Using Docker

With an interactive shell:

```shell
docker run -it -p 9000:9000 -e "MQTT_ADDRESS=192.168.0.1" kpetrem/mqtt-exporter
```

If you need the container to start on system boot (e.g. on your server/Raspberry Pi):

```shell
docker run -d -p 9000:9000 --restart unless-stopped --name mqtt-exporter  -e "MQTT_ADDRESS=192.168.0.1" kpetrem/mqtt-exporter
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
    restart: unless-stopped
```

#### Using Python

```
pip install -r requirements/base.txt
MQTT_ADDRESS=192.168.0.1 python exporter.py
```

#### Get the metrics on Prometheus

See below an example of Prometheus configuration to scrape the metrics:

```
scrape_configs:
  - job_name: mqtt-exporter
    static_configs:
      - targets: ["mqtt-exporter:9000"]
```

#### Nicer metrics

If you want nicer metrics, you can configure mqtt-exporter in your `docker-compose.yml` as followed:
```
version: "3"
services:
  mqtt-exporter:
    image: kpetrem/mqtt-exporter
    ports:
      - 9000:9000
    environment:
      - MQTT_ADDRESS=192.168.0.1
      - PROMETHEUS_PREFIX=sensor_
      - TOPIC_LABEL=sensor
    restart: unless-stopped
```

Result:
```
sensor_temperature{sensor="zigbee2mqtt_bedroom"} 22.3
```

And then remove `zigbee2mqtt_` prefix from `sensor` label via Prometheus configuration:

```
scrape_configs:
  - job_name: mqtt-exporter
    static_configs:
      - targets: ["mqtt-exporter:9000"]
    metric_relabel_configs:
      - source_labels: [sensor]
        regex: 'zigbee2mqtt_(.*)'
        replacement: '$1'
        target_label: sensor
```

Result:
```
sensor_temperature{sensor=bedroom"} 22.3
```

## Contribute

### Dev environment

You can install invoke package on your system and then use it to install environement, run an autoformat or just run the exporter:

  * `invoke install`: to install virtualenv under .venv/ and install all dev requirements
  * `invoke reformat`: reformat using black and isort
  * `invoke start`: start the app

### Coding style

Please ensure you have run the following before pushing a commit:
  * `black` and `isort` (or `invoke reformat`)
  * `pylama` to run all linters

Follow usual best practices:
  * document your code (inline and docstrings)
  * constant are in upper case
  * use comprehensible variable name
  * one function = one purpose
  * function name should define perfectly its purpose
