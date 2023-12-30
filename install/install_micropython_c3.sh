#!/bin/bash

set -e

FW_FILE=ESP32_GENERIC_C3-20231005-v1.21.0.bin


# get the firmware if it doesn't exist
if [ ! -f $FW_FILE ]; then
    wget https://micropython.org/resources/firmware/ESP32_GENERIC_C3-20231005-v1.21.0.bin
fi


# program
esptool.py --chip esp32c3 --port /dev/ttyACM0 --baud 921600 --before default_reset \
            --after hard_reset --no-stub  write_flash --flash_mode dio \
            --flash_freq 80m 0x0 $FW_FILE
