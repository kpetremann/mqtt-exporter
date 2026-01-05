# METRIC_TIMEOUT Feature

## Overview

This feature adds the ability to automatically remove metrics that haven't been updated within a specified timeout period. This is useful for cleaning up stale metrics from devices that have gone offline or stopped reporting.

## Configuration

Set the `METRIC_TIMEOUT` environment variable to specify the timeout in seconds:

```bash
# Set timeout to 300 seconds (5 minutes)
export METRIC_TIMEOUT=300
```

- **Default:** 0 (disabled - metrics are never removed)
- **Minimum:** 0 (disables the feature)
- **Recommended:** 300-3600 seconds (5 minutes to 1 hour), depending on your sensor update frequency

## How It Works

1. When a metric receives an update from MQTT, the current timestamp is recorded
2. A background cleanup thread runs periodically (at least every minute, or at the timeout interval if shorter)
3. During cleanup, any metric that hasn't been updated within the timeout period is removed from Prometheus
4. Both the main metric and its `_ts` timestamp metric (if `EXPOSE_LAST_SEEN` is enabled) are removed

## Usage Examples

### Docker Compose

```yaml
version: "3"
services:
  mqtt-exporter:
    image: kpetrem/mqtt-exporter
    ports:
      - 9000:9000
    environment:
      - MQTT_ADDRESS=192.168.0.1
      - METRIC_TIMEOUT=600  # Remove metrics after 10 minutes of no updates
```

### Docker Run

```bash
docker run -d \
  -p 9000:9000 \
  -e MQTT_ADDRESS=192.168.0.1 \
  -e METRIC_TIMEOUT=300 \
  kpetrem/mqtt-exporter
```

### Kubernetes Helm Chart

```yaml
env:
  - name: METRIC_TIMEOUT
    value: "600"
```

## Use Cases

- **Offline devices:** Automatically remove metrics from devices that have gone offline
- **Testing:** Clean up metrics from test devices that are no longer active
- **Dynamic environments:** Handle devices that are frequently added and removed
- **Resource optimization:** Reduce memory usage by removing stale metrics

## Behavior

- Metrics are only checked for expiration when the cleanup thread runs
- The cleanup runs at most once per minute, or at the timeout interval if it's shorter
- When a metric is removed, a log message is generated at INFO level
- If `METRIC_TIMEOUT=0` (default), no cleanup is performed and metrics persist indefinitely

## Logging

When a metric expires, you'll see log entries like:

```
INFO:mqtt-exporter:Removed expired metric: PromMetricId(name='mqtt_temperature', labels=()) with labels {'topic': 'sensor1'}
```

## Considerations

- Choose a timeout value longer than your sensor's normal update interval
- Consider network reliability and potential delays when setting the timeout
- Very short timeouts (< 60 seconds) may cause metrics to flap if updates are irregular
- The cleanup thread is a daemon thread and will automatically stop when the exporter exits
