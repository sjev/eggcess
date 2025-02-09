#!/bin/bash

set -e

PORT=/dev/ttyACM0
FW_FILE=adafruit-circuitpython-seeed_xiao_esp32c3-en_US-9.2.4.bin

# erase
esptool.py --chip esp32c3 --port $PORT erase_flash


# program
esptool.py --chip esp32c3 --port $PORT --baud 921600 write_flash -z 0x0 $FW_FILE
