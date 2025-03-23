#!/bin/bash

set -e
source .secrets.sh

# Check required env variables
if [ -z "$MQTT_USER" ] || [ -z "$MQTT_PASS" ]; then
  echo "Error: MQTT_USER and/or MQTT_PASS environment variables are not set."
  exit 1
fi

counter=1

while true; do
  message="Test message $counter"
  mosquitto_pub -h 192.168.1.100 -t /test/cmd -m "$message" -u "$MQTT_USER" -P "$MQTT_PASS"
  echo "Published: $message"
  counter=$((counter + 1))
  sleep 1

  # send open command
  echo "Sending open command"
  mosquitto_pub -h 192.168.1.100 -t $MQTT_ROOT/cmd -m "open" -u "$MQTT_USER" -P "$MQTT_PASS"

  sleep 30
  # send close command
  echo "Sending close command"
  mosquitto_pub -h 192.168.1.100 -t $MQTT_ROOT/cmd -m "close" -u "$MQTT_USER" -P "$MQTT_PASS"
  sleep 30

done
