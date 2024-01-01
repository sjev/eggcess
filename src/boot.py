# This is script that run when device boot up or wake from sleep.
import machine
import webrepl
import network
import time
import ntptime

import my_secrets as secrets


# Set up the Wi-Fi interface
wifi = network.WLAN(network.STA_IF)
wifi.active(True)

# Connect to the network
wifi.connect(secrets.SSID, secrets.WIFI_PASSWORD)

# Wait for the connection to establish
while not wifi.isconnected():
    print("connecting to wifi...")
    time.sleep(1)

# Print the network's IP address (if connected)
if wifi.isconnected():
    print("Connected to wifi")
    print(f"IP address: {wifi.ifconfig()[0]}")
    print(f"Signal strength: {wifi.status('rssi')} dBm")

    # display mac address
    mac = wifi.config("mac")
    print("MAC address:", ":".join("{:02x}".format(x) for x in mac))

else:
    print("Could not connect to wifi, rebooting")
    time.sleep(1)
    machine.reset()

# Sync time with NTP server, wait until connected
success = False
while not success:
    try:
        ntptime.settime()
        success = True
    except OSError:
        print("Error updating time, retrying...")
        time.sleep(1)


# Start the web REPL
print("Starting web REPL")
webrepl.start()
