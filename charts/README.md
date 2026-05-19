# MQTT-exporter Charts
![Release Charts](https://github.com/longhorn/charts/workflows/Release%20Charts/badge.svg)

This repository contains the charts used for installing MQTT-exporter using Helm. Currently, this chart only contains the following chart:
- `mqtt-exporter` - The chart for MQTT-exporter. For the actual MQTT-exporter repository, go [here]([https://github.com/longhorn/longhorn](https://github.com/kpetremann/mqtt-exporter)).

## Adding the Chart
```
$ helm repo add longhorn https://kpetremann.github.io/mqtt-exporter
$ helm repo update
```
