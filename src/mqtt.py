import wifi
import socketpool
import time
import adafruit_minimqtt.adafruit_minimqtt as mqtt

import my_secrets as secrets


def connect(mqtt_client, userdata, flags, rc):
    # This function will be called when the mqtt_client is connected
    # successfully to the broker.
    print(f"Connected to MQTT Broker! {flags=}, {rc=}")


def disconnect(mqtt_client, userdata, rc):
    # This method is called when the mqtt_client disconnects
    # from the broker.
    print("Disconnected from MQTT Broker!")


def subscribe(mqtt_client, userdata, topic, granted_qos):
    # This method is called when the mqtt_client subscribes to a new feed.
    print(f"Subscribed to {topic} with QOS level {granted_qos}")


def unsubscribe(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client unsubscribes from a feed.
    print(f"mqtt unsubscribed from {topic} with pid {pid}")


def get_client(on_message=None):
    """client factory"""
    pool = socketpool.SocketPool(wifi.radio)
    print(f"Connecting to {secrets.MQTT_BROKER}")

    client = mqtt.MQTT(
        broker=secrets.MQTT_BROKER,
        username=secrets.MQTT_USER,
        password=secrets.MQTT_PASSWORD,
        socket_pool=pool,
    )

    # Connect callback handlers to mqtt_client
    client.on_connect = connect
    client.on_disconnect = disconnect
    client.on_subscribe = subscribe
    client.on_unsubscribe = unsubscribe

    if on_message:
        client.on_message = on_message

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
