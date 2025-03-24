#!/bin/bash
# provie commmand as parameter
# ./send_command.sh open
set -e
source .secrets.sh

# Check if command is provided
if [ -z "$1" ]; then
  echo "Error: Command is not provided."
  exit 1
fi

# Check required env variables
if [ -z "$MQTT_USER" ] || [ -z "$MQTT_PASS" ]; then
  echo "Error: MQTT_USER and/or MQTT_PASS environment variables are not set."
  exit 1
fi

# send open command
echo "Sending open command $1 to $MQTT_ROOT/cmd"
mosquitto_pub -h $MQTT_HOST -t $MQTT_ROOT/cmd -m "$1" -u "$MQTT_USER" -P "$MQTT_PASS"
