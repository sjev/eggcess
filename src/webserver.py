import asyncio
import wifi
from logger import LOG_FILE


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
    # Skip HTTP request headers
    while await reader.readline() != b"\r\n":
        pass

    log_contents = read_log()

    # Send plain text response
    writer.write("HTTP/1.0 200 OK\r\nContent-type: text/plain\r\n\r\n")
    writer.write(log_contents)

    await writer.drain()
    writer.close()
    await writer.wait_closed()
    print("Client disconnected")


# -----------------testing----------------------
async def serve():

    print("Setting up webserver...")
    print("IP address:", wifi.radio.ipv4_address)

    asyncio.create_task(asyncio.start_server(serve_client, "0.0.0.0", 80))

    counter = 0
    while True:
        print(f"heartbeat {counter}")
        counter += 1
        await asyncio.sleep(5)


def test():
    asyncio.run(serve())
