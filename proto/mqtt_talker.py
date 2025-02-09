import os


import asyncio
import wifi
import gc
import time
import socketpool
import adafruit_minimqtt.adafruit_minimqtt as mqtt


T_START = time.time()

# -----------------------------
print("Testing mqtt")


broker = os.getenv("MQTT_BROKER")
user = os.getenv("MQTT_USER")
passwd = os.getenv("MQTT_PASS")

# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)
# ssl_context = ssl.create_default_context()


print(f"Connecting to {broker}")

client = mqtt.MQTT(broker=broker, username=user, password=passwd, socket_pool=pool)
client.connect()

print(f"{client.is_connected()}")


async def send_status():
    topic = "/test"
    counter = 0
    while True:

        uptime = time.time() - T_START
        msg = {
            "count": counter,
            "uptime_h": round(uptime / 3600, 3),
            "mem_free": gc.mem_free(),
        }
        print(f"Sending {msg}")
        client.publish(topic, str(msg))
        counter += 1
        await asyncio.sleep(1)


async def main():

    coros = [send_status()]

    await asyncio.gather(*coros)


# Start the main loop
asyncio.run(main())
