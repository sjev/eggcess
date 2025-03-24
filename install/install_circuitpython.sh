#!/bin/bash

set -e

FW_VERSION="9.2.6"

FW_URL=https://downloads.circuitpython.org/bin/seeed_xiao_esp32c3/en_US/adafruit-circuitpython-seeed_xiao_esp32c3-en_US-$FW_VERSION.bin

PORT=/dev/ttyACM0

# download
FW_FILE=$(basename $FW_URL)
if [ ! -f $FW_FILE ]; then
    echo "Downloading $FW_FILE"
    wget $FW_URL
fi

# erase
esptool.py --chip esp32c3 --port $PORT erase_flash

# program
esptool.py --chip esp32c3 --port $PORT --baud 921600 write_flash -z 0x0 $FW_FILE
