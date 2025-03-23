import os
import wifi
import socketpool
import time
import adafruit_minimqtt.adafruit_minimqtt as mqtt
import logger

DEVICE_NAME = os.getenv("CIRCUITPY_WEB_INSTANCE_NAME", "eggcess")
CMD_TOPIC = os.getenv("CMD_TOPIC", f"/{DEVICE_NAME}/cmd")


def on_connect(mqtt_client, userdata, flags, rc):
    # This function will be called when the mqtt_client is connected
    # successfully to the broker.
    logger.info(f"Connected to MQTT Broker. {flags=}, {rc=}")
    if CMD_TOPIC is not None:
        logger.debug(f"Subscribing to {CMD_TOPIC}")
        mqtt_client.subscribe(CMD_TOPIC)


def on_disconnect(mqtt_client, userdata, rc):
    # This method is called when the mqtt_client disconnects
    # from the broker.
    logger.info("Disconnected from MQTT Broker.")


def on_subscribe(mqtt_client, userdata, topic, granted_qos):
    # This method is called when the mqtt_client subscribes to a new feed.
    logger.info(f"Subscribed to {topic} with QOS level {granted_qos}")


def unsubscribe(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client unsubscribes from a feed.
    logger.info(f"mqtt unsubscribed from {topic} with pid {pid}")


def get_client(on_message=None):
    """client factory"""
    pool = socketpool.SocketPool(wifi.radio)

    mqtt_broker = os.getenv("MQTT_BROKER")
    mqtt_user = os.getenv("MQTT_USER")
    mqtt_pass = os.getenv("MQTT_PASS")

    # check that the environment variables are set
    if not all([mqtt_broker, mqtt_user, mqtt_pass]):
        raise ValueError("MQTT_BROKER, MQTT_USER, and MQTT_PASS must be set")

    client = mqtt.MQTT(
        broker=mqtt_broker,
        username=mqtt_user,
        password=mqtt_pass,
        socket_pool=pool,
    )

    # Connect callback handlers to mqtt_client
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe
    client.on_unsubscribe = unsubscribe

    if on_message:
        client.on_message = on_message

    return client


# ------------------testing functions------------------
def echo_message(client, topic, message):
    logger.debug(f"New message on {topic}: {message}")
    client.publish("/test/echo", message)


def test() -> None:
    """Test the mqtt module"""

    print("Testing mqtt")

    global CMD_TOPIC
    CMD_TOPIC = "/test/cmd"

    client = get_client(on_message=echo_message)
    client.connect()

    logger.debug(f"{client.is_connected()=}")

    for counter in range(10):

        client.loop(timeout=1.0)
        msg = {"count": counter}
        print(f"Sending {msg}")
        client.publish("/test/heartbeat", str(msg))


if __name__ == "__main__":
    test()
