#!/bin/bash

set -e
source .secrets.sh

# Check required env variables
if [ -z "$MQTT_USER" ] || [ -z "$MQTT_PASS" ]; then
  echo "Error: MQTT_USER and/or MQTT_PASS environment variables are not set."
  exit 1
fi

mosquitto_sub -t $MQTT_ROOT/# -v -h 192.168.1.100 -u $MQTT_USER -P $MQTT_PASS
