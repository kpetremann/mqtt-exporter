# MQTT-exporter Charts
[![Helm chart release](https://github.com/kpetremann/mqtt-exporter/actions/workflows/helm-release.yml/badge.svg)](https://github.com/kpetremann/mqtt-exporter/actions/workflows/helm-release.yml)

This repository contains the charts used for installing MQTT-exporter using Helm. Currently, this chart only contains the following chart:
- `mqtt-exporter` - The chart for MQTT-exporter. For the actual MQTT-exporter repository, go [here](https://github.com/kpetremann/mqtt-exporter).

## Adding the Chart
```
$ helm repo add longhorn https://kpetremann.github.io/mqtt-exporter
$ helm repo update
```
