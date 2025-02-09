import os
import time
import wifi
import gc
import socketpool
import adafruit_minimqtt.adafruit_minimqtt as mqtt

T_START = time.time()
CMD_TOPIC = "/test_cmd"

# Setup MQTT from environment variables
broker = os.getenv("MQTT_BROKER")
user = os.getenv("MQTT_USER")
passwd = os.getenv("MQTT_PASS")


# ----- MQTT Callbacks -----
def on_connect(client, userdata, flags, rc):
    client.subscribe(CMD_TOPIC)


def on_disconnect(client, userdata, rc):
    print("Client disconnected")


def on_message(client, topic, message):
    print(f"New message on {topic}: {message}")
    client.publish("/test", message)


pool = socketpool.SocketPool(wifi.radio)
client = mqtt.MQTT(broker=broker, username=user, password=passwd, socket_pool=pool)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

print(f"Connecting to {broker}")
client.connect()
print("Connected:", client.is_connected())


# ----- Scheduler Class -----
class Scheduler:
    def __init__(self):
        # Each task: [interval_in_seconds, last_run_time, function]
        self.tasks = []

    def add_task(self, interval, func):
        self.tasks.append([interval, time.time(), func])

    def run(self):
        now = time.time()
        for task in self.tasks:
            interval, last_run, func = task
            if now - last_run >= interval:
                func()
                task[1] = now  # Update last_run


# ----- Periodic Task Functions -----
def task_5_sec():
    print("Running 5-second task!")


def task_10_sec():
    print("Running 10-second task!")


def send_status(client, counter):
    uptime = time.time() - T_START
    msg = {
        "count": counter,
        "uptime_h": round(uptime / 3600, 3),
        "mem_free": gc.mem_free(),
    }
    print("Sending", msg)
    client.publish("/test", str(msg))


# ----- Main Function -----
def main():

    # Setup scheduler and add periodic tasks
    scheduler = Scheduler()

    scheduler.add_task(5, task_5_sec)
    scheduler.add_task(10, task_10_sec)

    counter = 0
    while True:
        client.loop(timeout=1)
        send_status(client, counter)
        counter += 1
        scheduler.run()
        time.sleep(1)


if __name__ == "__main__":
    main()
