import wifi
import socketpool
import time
import adafruit_minimqtt.adafruit_minimqtt as mqtt

import my_secrets as secrets


def get_client():
    """client factory"""
    pool = socketpool.SocketPool(wifi.radio)
    print(f"Connecting to {secrets.MQTT_BROKER}")

    client = mqtt.MQTT(
        broker=secrets.MQTT_BROKER,
        username=secrets.MQTT_USER,
        password=secrets.MQTT_PASSWORD,
        socket_pool=pool,
    )
    client.connect()
    return client


# -----------------------------
def test() -> None:
    """Test the mqtt module"""

    print("Testing mqtt")

    TOPIC = "/test"

    client = get_client()

    print(f"{client.is_connected()}")

    for counter in range(10):
        msg = {"count": counter}
        print(f"Sending {msg}")
        client.publish(TOPIC, str(msg))
        time.sleep(0.1)
