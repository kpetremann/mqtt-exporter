#!/bin/env python3

"""
MQTT Prometheus exporter

You can run it with

```sh
python -m pip install mqtt-exporter
python -m mqtt_exporter
```

"""

from .main import main_mqtt_exporter

if __name__ == "__main__":
    main_mqtt_exporter()
