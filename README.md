![CI](https://github.com/kpetremann/mqtt-exporter/actions/workflows/ci.yml/badge.svg)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/b1ca990b576342a48d771d472e64bc24)](https://www.codacy.com/app/kpetremann/mqtt-exporter?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=kpetremann/mqtt-exporter&amp;utm_campaign=Badge_Grade)
[![Maintainability](https://api.codeclimate.com/v1/badges/635c98a1b4701d1ab4cf/maintainability)](https://codeclimate.com/github/kpetremann/mqtt-exporter/maintainability)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![Build and publish docker images](https://github.com/kpetremann/mqtt-exporter/actions/workflows/docker-release.yml/badge.svg)](https://hub.docker.com/r/kpetrem/mqtt-exporter)

[![](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/kpetremann)

<a href="https://www.buymeacoffee.com/kpetremann" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

# MQTT-exporter

## Description

Simple and generic Prometheus exporter for MQTT.
Tested with Mosquitto MQTT and Xiaomi sensors.

It exposes metrics from MQTT message out of the box. You just need to specify the target if not on localhost.

MQTT-exporter expects a topic and a flat JSON payload, the value must be numeric values.

It also provides message counters for each MQTT topic:
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
  * Shelly power sensors (3EM - only with `KEEP_FULL_TOPIC` enabled)

It is also being used by users on:
  * https://github.com/jomjol/AI-on-the-edge-device
  * https://github.com/kbialek/deye-inverter-mqtt

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

**Important notice: legacy availability payload is not supported and must be disabled** - see [Device availability advanced](https://www.zigbee2mqtt.io/guide/configuration/device-availability.html#availability-payload)

When exposing device availability, Zigbee2MQTT add /availability suffix in the topic. So we end up with inconsistent metrics:

```
mqtt_state{topic="zigbee2mqtt_garage_availability"} 1.0
mqtt_temperature{topic="zigbee2mqtt_garage"} 1.0
```

To avoid having different topics for the same device, the exporter has a normalization feature disabled by default.
It can be enabled by setting ZIGBEE2MQTT_AVAILABILITY varenv to "True".

It will remove the suffix from the topic and change the metric name accordingly:

```
mqtt_zigbee_availability{topic="zigbee2mqtt_garage"} 1.0
mqtt_temperature{topic="zigbee2mqtt_garage"} 1.0
```

Note: the metric name mqtt_state is not kept reducing collision risks as it is too common.

### Zwavejs2Mqtt

This exporter also supports Zwavejs2Mqtt metrics, preferably using "named topics" (see [official documentation](https://zwave-js.github.io/zwavejs2mqtt/#/usage/setup?id=gateway)).

To set up this, you need to specify the topic prefix used by Zwavejs2Mqtt in `ZWAVE_TOPIC_PREFIX` the environment variable (default being "zwave/").

### ESPHome

ESPHome is supported only when using the default `state_topic`: `<TOPIC_PREFIX>/<COMPONENT_TYPE>/<COMPONENT_NAME>/state`. (see [official documentation](https://esphome.io/components/mqtt.html#mqtt-component-base-configuration)).

To set up this, you need to specify the topic prefix list used by ESPHome in `ESPHOME_TOPIC_PREFIXES` the environment variable (default being "", so disabled).

This is a list so you can simply set one or more topic prefixes, the separator being a comma.

Example: `ESPHOME_TOPIC_PREFIXES="esphome-weather-indoor,esphome-weather-outdoor"`

If all of your ESPHome topics share a same prefix, you can simply put the common part. In the above example, `"esphome"` will match all topic starting by "esphome".

### Hubitat

Hubitat is supported. By default all topic starting with `hubitat/` will be identified and parsed as Hubitat messages.

Topics look like `hubitat/<hubname>/<device>/attributes/<attribute>/value`.

Like for ESPHome, `HUBITAT_TOPIC_PREFIXES` is a list with `,` as a separator.

### Configuration

Parameters are passed using environment variables.

The list of parameters are:
  * `KEEP_FULL_TOPIC`: Keep entire topic instead of the first two elements only. Usecase: Shelly 3EM (default: False)
  * `LOG_LEVEL`: Logging level (default: INFO)
  * `LOG_MQTT_MESSAGE`: Log MQTT original message, only if LOG_LEVEL is set to DEBUG (default: False)
  * `MQTT_IGNORED_TOPICS`: Comma-separated lists of topics to ignore. Accepts wildcards. (default: None)
  * `MQTT_ADDRESS`: IP or hostname of MQTT broker (default: 127.0.0.1)
  * `MQTT_PORT`: TCP port of MQTT broker (default: 1883)
  * `MQTT_TOPIC`: Comma-separated lists of topics to subscribe to (default: #)
  * `MQTT_KEEPALIVE`: Keep alive interval to maintain connection with MQTT broker (default: 60)
  * `MQTT_USERNAME`: Username which should be used to authenticate against the MQTT broker (default: None)
  * `MQTT_PASSWORD`: Password which should be used to authenticate against the MQTT broker (default: None)
  * `MQTT_V5_PROTOCOL`: Force to use MQTT protocol v5 instead of 3.1.1
  * `MQTT_CLIENT_ID`: Set client ID manually for MQTT connection
  * `MQTT_EXPOSE_CLIENT_ID`: Expose the client ID as a label in Prometheus metrics
  * `MQTT_ENABLE_TLS`: Enable TLS for MQTT connection (default: False)
  * `MQTT_TLS_NO_VERIFY`: Disable TLS certificate verification (default: False)
  * `MQTT_TLS_CA_CERT`: Path to custom CA certificate file for TLS (default: None, uses system CA)
  * `MQTT_TLS_CLIENT_CERT`: Path to client certificate file for mTLS client authentication (default: None)
  * `MQTT_TLS_CLIENT_KEY`: Path to client private key file for mTLS client authentication (default: None)
  * `PROMETHEUS_ADDRESS`: HTTP server address to expose Prometheus metrics on (default: 0.0.0.0)
  * `PROMETHEUS_PORT`: HTTP server PORT to expose Prometheus metrics (default: 9000)
  * `PROMETHEUS_PREFIX`: Prefix added to the metric name, example: mqtt_temperature (default: mqtt_)
  * `TOPIC_LABEL`: Define the Prometheus label for the topic, example temperature{topic="device1"} (default: topic)
  * `ZIGBEE2MQTT_AVAILABILITY`: Normalize sensor name for device availability metric added by Zigbee2MQTT (default: False)
  * `ZWAVE_TOPIC_PREFIX`: MQTT topic used for Zwavejs2Mqtt messages (default: zwave/)
  * `ESPHOME_TOPIC_PREFIXES`: MQTT topic used for ESPHome messages (default: "")
  * `HUBITAT_TOPIC_PREFIXES`: MQTT topic used for Hubitat messages (default: "hubitat/")
  * `EXPOSE_LAST_SEEN`: Enable additional gauges exposing last seen timestamp for each metrics
  * `PARSE_MSG_PAYLOAD`: Enable parsing and metrics of the payload. (default: true)
  * `MAX_METRICS`: Maximum number of metrics to create. When limit is reached, new metrics will be ignored. Set to 0 for unlimited. (default: 2000)

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

## Docker-compose full stack example

This docker-compose aims to share a typical monitoring stack.

If you need persistent metrics, I would advise using VictoriaMetrics. Of course there are other suitable persistent storage solutions for Prometheus.

[docker-compose.yaml](https://github.com/kpetremann/mqtt-exporter/blob/master/doc/example/docker-compose.yml)

You can also add other cool software such as Home-Assistant.

## CLI interactive test

You can use the test mode to preview the conversion of a topic and payload to Prometheus metrics.

Usage example:

```
$ python ./exporter.py --test
topic: zigbee2mqtt/0x00157d00032b1234
payload: {"temperature":26.24,"humidity":45.37}

## Debug ##

parsed to: zigbee2mqtt_0x00157d00032b1234 {'temperature': 26.24, 'humidity': 45.37}
INFO:mqtt-exporter:creating prometheus metric: PromMetricId(name='mqtt_temperature', labels=())
INFO:mqtt-exporter:creating prometheus metric: PromMetricId(name='mqtt_humidity', labels=())

## Result ##

# HELP mqtt_temperature metric generated from MQTT message.
# TYPE mqtt_temperature gauge
mqtt_temperature{topic="zigbee2mqtt_0x00157d00032b1234"} 26.24
# HELP mqtt_humidity metric generated from MQTT message.
# TYPE mqtt_humidity gauge
mqtt_humidity{topic="zigbee2mqtt_0x00157d00032b1234"} 45.37
```

## Contribute

See [CONTRIBUTING.md](./CONTRIBUTING.md).

### Support

If you like my work, don't hesitate to buy me a coffee :)

<a href="https://www.buymeacoffee.com/kpetremann" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

[![](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/kpetremann)
