from machine import Pin
import uasyncio as asyncio
import network
from logger import LOG_FILE

onboard = Pin(3, Pin.OUT, value=0)

html = """<!DOCTYPE html>
<html>
    <head> <title>Eggcess</title> </head>
    <body> <h1>Eggcess log</h1>
        <pre>%s</pre>
    </body>
</html>
"""

wlan = network.WLAN(network.STA_IF)


def read_log():
    try:
        with open(LOG_FILE, "r") as file:
            return file.read()
    except OSError:
        return "Log file not found."


async def serve_client(reader, writer):
    print("Client connected")
    request_line = await reader.readline()
    print("Request:", request_line)
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass

    log_contents = read_log()

    response = html % log_contents
    writer.write("HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n")
    writer.write(response)

    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")


async def demo():
    print("Setting up webserver...")
    ip = wlan.ifconfig()[0]
    print("IP address:", ip)

    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))
    while True:
        onboard.on()
        print("heartbeat")
        await asyncio.sleep(0.25)
        onboard.off()
        await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(demo())
    except Exception as e:
        print("Exited with exception:", e)
