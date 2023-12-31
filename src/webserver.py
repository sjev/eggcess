import network


from machine import Pin
import uasyncio as asyncio

led = Pin(2, Pin.OUT)
onboard = Pin(3, Pin.OUT, value=0)

html = """<!DOCTYPE html>
<html>
    <head> <title>Pico W</title> </head>
    <body> <h1>Pico W</h1>
        <p>%s</p>
    </body>
</html>
"""

wlan = network.WLAN(network.STA_IF)


async def serve_client(reader, writer):
    print("Client connected")
    request_line = await reader.readline()
    print("Request:", request_line)
    # We are not interested in HTTP request headers, skip them
    while await reader.readline() != b"\r\n":
        pass

    request = str(request_line)
    led_on = request.find("/light/on")
    led_off = request.find("/light/off")
    print("led on = " + str(led_on))
    print("led off = " + str(led_off))

    stateis = ""
    if led_on == 6:
        print("led on")
        led.value(1)
        stateis = "LED is ON"

    if led_off == 6:
        print("led off")
        led.value(0)
        stateis = "LED is OFF"

    response = html % stateis
    writer.write("HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n")
    writer.write(response)

    await writer.drain()
    await writer.wait_closed()
    print("Client disconnected")


async def main():
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


try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
