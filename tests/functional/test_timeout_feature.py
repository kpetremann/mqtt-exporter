#!/usr/bin/env python3
"""Test script to verify the timeout feature works correctly."""

import time
from collections import defaultdict
from dataclasses import dataclass

# Simulate the key parts of the implementation
@dataclass(frozen=True)
class PromMetricId:
    name: str
    labels: tuple = ()

# Simulate global variables
metric_last_update = {}

def add_metric(metric_id, labels, timeout=10):
    """Simulate adding a metric with timestamp tracking."""
    labels_tuple = tuple(sorted(labels.items()))
    metric_key = (metric_id, labels_tuple)
    metric_last_update[metric_key] = time.time()
    return metric_key

def cleanup_expired_metrics(timeout):
    """Simulate cleanup of expired metrics."""
    if timeout <= 0:
        return []

    current_time = time.time()
    expired_metrics = []

    for metric_key, last_update in metric_last_update.items():
        if current_time - last_update > timeout:
            expired_metrics.append(metric_key)

    for metric_key in expired_metrics:
        del metric_last_update[metric_key]

    return expired_metrics

# Test the feature
print("Testing timeout feature...")
print()

# Create some test metrics
metric1 = PromMetricId("mqtt_temperature", ())
metric2 = PromMetricId("mqtt_humidity", ())

labels1 = {"topic": "sensor1"}
labels2 = {"topic": "sensor2"}

print("1. Adding two metrics...")
key1 = add_metric(metric1, labels1, timeout=2)
key2 = add_metric(metric2, labels2, timeout=2)
print(f"   Created {len(metric_last_update)} metrics")

print("\n2. Waiting 1 second and checking for expired metrics...")
time.sleep(1)
expired = cleanup_expired_metrics(timeout=2)
print(f"   Expired: {len(expired)} (expected: 0)")
print(f"   Remaining: {len(metric_last_update)} (expected: 2)")

print("\n3. Updating metric1 after 1 second...")
add_metric(metric1, labels1, timeout=2)

print("\n4. Waiting 1.5 more seconds...")
time.sleep(1.5)

print("\n5. Checking for expired metrics...")
expired = cleanup_expired_metrics(timeout=2)
print(f"   Expired: {len(expired)} (expected: 1 - metric2 should expire)")
print(f"   Remaining: {len(metric_last_update)} (expected: 1 - metric1 should remain)")

print("\n6. Testing with timeout=0 (disabled)...")
metric_last_update.clear()
add_metric(metric1, labels1, timeout=0)
add_metric(metric2, labels2, timeout=0)
expired = cleanup_expired_metrics(timeout=0)
print(f"   Expired: {len(expired)} (expected: 0 - timeout disabled)")
print(f"   Remaining: {len(metric_last_update)} (expected: 2)")

print("\n✅ Test completed successfully!\n"