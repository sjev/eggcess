#!/bin/bash

set -e

FW_FILE=adafruit-circuitpython-seeed_xiao_esp32c3-en_US-9.0.4.bin


# program
esptool.py --chip esp32c3 --port /dev/ttyACM0 --baud 921600 --before default_reset \
            --after hard_reset --no-stub  write_flash --flash_mode dio \
            --flash_freq 80m 0x0 $FW_FILE
