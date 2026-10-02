import asyncio
import base64
import os
import sys
import time
from pathlib import Path
from fnmatch import fnmatch
from click import prompt
import requests
import websockets
from invoke import task


def get_secrets() -> dict[str, str]:
    """Get secrets from environment variables."""
    keys = ["DEVICE_IP", "DEVICE_PASS"]
    secrets = {key: os.getenv(key) for key in keys}

    # Check that all secrets are present
    for k, v in secrets.items():
        if v is None:
            sys.exit(f"Error: Missing secret for {k}")

    return {k: v for k, v in secrets.items() if k is not None and v is not None}


def read_syncignore():
    """Read the .syncignore file and return a list of patterns to ignore."""
    ignore_file = Path(".syncignore")
    if ignore_file.exists():
        with ignore_file.open("r") as file:
            # Read each line, strip whitespace, ignore empty and commented lines
            return [
                line.strip()
                for line in file
                if line.strip() and not line.startswith("#")
            ]
    return []


@task
def clean(ctx):
    """
    Remove all files and directories that are not under version control to ensure a pristine working environment.
    Use caution as this operation cannot be undone and might remove untracked files.

    """

    ctx.run("git clean -nfdx")

    if (
        prompt(
            "Are you sure you want to remove all untracked files? (y/n)", default="n"
        )
        == "y"
    ):
        ctx.run("git clean -fdx")


@task
def put(ctx, src: str, dest: str) -> None:
    """
    Upload a single file to the device. (invoke put --src=myfile.txt --dest=/remote/path/newname.txt)

    """
    secrets = get_secrets()
    base_url = f"http://{secrets['DEVICE_IP']}/fs/"
    auth = ("", secrets["DEVICE_PASS"])
    file_path = Path(src)

    if not file_path.exists():
        print(f"File {src} does not exist")
        return

    # Determine remote path
    if dest.endswith("/"):
        remote_path = f"{dest}{file_path.name}"
    else:
        remote_path = dest

    # Ensure correct path separators
    remote_path = remote_path.replace("\\", "/")

    with file_path.open("rb") as file:
        file_content = file.read()
        headers = {"Content-Type": "application/octet-stream"}
        response = requests.put(
            f"{base_url}{remote_path}", data=file_content, auth=auth, headers=headers
        )

        if response.status_code in [200, 201, 204]:
            print(f"Successfully uploaded {file_path} to {remote_path}")
        else:
            print(
                f"Failed to upload {file_path} to {remote_path}: {response.status_code} - {response.reason}"
            )


@task
def pull(ctx, dest="src/", src="/"):
    """
    Get files from device, dest is the local directory, src is the remote directory.
    """
    secrets = get_secrets()
    base_url = f"http://{secrets['DEVICE_IP']}/fs/"
    auth = ("", secrets["DEVICE_PASS"])
    ignore_patterns = read_syncignore()

    response = requests.get(
        f"{base_url}{src}", auth=auth, headers={"Accept": "application/json"}
    )
    if response.status_code == 200:
        dir_info = response.json()
        if "files" in dir_info:
            for file_info in dir_info["files"]:
                if (
                    not file_info["directory"]
                    and not file_info["name"].startswith(".")
                    and all(
                        not fnmatch(file_info["name"], pat) for pat in ignore_patterns
                    )
                ):
                    device_path = f"{src}{file_info['name']}"
                    local_path = os.path.join(dest, file_info["name"])
                    response = requests.get(f"{base_url}{device_path}", auth=auth)
                    if response.status_code == 200:
                        os.makedirs(os.path.dirname(local_path), exist_ok=True)
                        with open(local_path, "wb") as file:
                            file.write(response.content)
                        print(f"Downloaded {device_path} to {local_path}")


@task
def upload_src(ctx):
    """upload all source files"""

    # upload files from src
    files = Path("src").glob("*.py")
    for file in files:
        # skip .example files
        if "example" in file.name:
            print(f"Skipping {file}")
            continue

        print(f"Uploading {file}...")
        ctx.run(f"ampy put {file}")
        print(f"Uploaded {file}")

    print("Done")


@task
def upload_lut(ctx):
    """upload the sun_lut.csv file"""
    f = Path("calculations/sun_lut.csv")
    assert f.exists(), f"File {f} does not exist"
    print(f"Uploading {f}...")
    ctx.run(f"ampy put {f}")

    print("Done")


HW_TEST_DIR = "test"
REPL_TIMEOUT_S = 30  # to stop main.py and reach the prompt
RUN_TIMEOUT_S = 180  # for run.py up to the Wi-Fi test
IDLE_TIMEOUT_S = 60  # max silence on the console while run.py runs
RESULTS_TIMEOUT_S = 120  # for Wi-Fi to come back and results.txt to show DONE
RESTART_TIMEOUT_S = 60  # for production code to log its start


def _ws_connect(ip: str, password: str):
    auth = base64.b64encode(f":{password}".encode()).decode()
    # CircuitPython does not answer websocket pings
    return websockets.connect(
        f"ws://{ip}/cp/serial/",
        additional_headers={"Authorization": f"Basic {auth}"},
        ping_interval=None,
        open_timeout=10,
    )


async def _read_until(ws, markers: tuple[str, ...], timeout: float, idle: float) -> str:
    """Read console output until a marker shows, `timeout` passes, or it is silent for `idle`."""
    out = ""
    deadline = time.monotonic() + timeout
    try:
        while not any(m in out for m in markers):
            wait = min(idle, deadline - time.monotonic())
            if wait <= 0:
                break
            chunk = await asyncio.wait_for(ws.recv(), wait)
            print(chunk, end="", flush=True)
            out += chunk
    except (asyncio.TimeoutError, websockets.ConnectionClosed):
        pass
    return out


async def _run_on_repl(ip: str, password: str, cmd: str) -> str:
    """Stop main.py, run `cmd` at the REPL, return its output."""
    async with _ws_connect(ip, password) as ws:
        print("[hw-test] stopping main.py")
        deadline = time.monotonic() + REPL_TIMEOUT_S
        while True:
            if time.monotonic() > deadline:
                raise TimeoutError("no REPL prompt")
            await ws.send("\x03")
            out = await _read_until(ws, (">>> ", "Press any key"), timeout=3, idle=3)
            if "Press any key" in out:
                await ws.send("\r")
                out += await _read_until(ws, (">>> ",), timeout=5, idle=5)
            if ">>> " in out:
                break

        print("\n[hw-test] running run.py")
        await ws.send(cmd + "\r")
        # a new prompt means run.py ended early, also on a crash
        return await _read_until(
            ws, ("WIFI_DROP", "\n>>> "), timeout=RUN_TIMEOUT_S, idle=IDLE_TIMEOUT_S
        )


async def _restart_production(ip: str, password: str) -> None:
    async with _ws_connect(ip, password) as ws:
        print("\n[hw-test] restarting production code")
        await ws.send("\x04")
        out = await _read_until(ws, ("system start",), RESTART_TIMEOUT_S, RESTART_TIMEOUT_S)
    if "system start" not in out:
        print("[hw-test] WARNING: production start not seen, check the device")


def _wait_for_results(base_url: str, auth: tuple[str, str]) -> str:
    """Poll results.txt: the Wi-Fi test drops the console."""
    print("\n[hw-test] waiting for results.txt")
    deadline = time.monotonic() + RESULTS_TIMEOUT_S
    text = ""
    while time.monotonic() < deadline:
        try:
            r = requests.get(f"{base_url}{HW_TEST_DIR}/results.txt", auth=auth, timeout=5)
            text = r.text if r.ok else text
            if "DONE" in text:
                break
        except requests.RequestException:
            pass
        time.sleep(5)
    return text


@task
def hw_test(ctx):
    """Stage src/ and hw_tests/run.py in /test on the device, run them over Wi-Fi, restore production code."""
    secrets = get_secrets()
    ip, password = secrets["DEVICE_IP"], secrets["DEVICE_PASS"]
    base_url = f"http://{ip}/fs/"
    auth = ("", password)

    requests.put(f"{base_url}{HW_TEST_DIR}/", auth=auth, timeout=10)
    # remove old results, so a stale file never passes
    requests.delete(f"{base_url}{HW_TEST_DIR}/results.txt", auth=auth, timeout=10)
    for file in [*Path("src").glob("*.py"), Path("hw_tests/run.py")]:
        r = requests.put(
            f"{base_url}{HW_TEST_DIR}/{file.name}", data=file.read_bytes(), auth=auth, timeout=10
        )
        r.raise_for_status()
        print(f"[hw-test] staged {file}")

    cmd = f"import sys; sys.path.insert(0, '/{HW_TEST_DIR}'); import run"
    results = ""
    try:
        out = asyncio.run(_run_on_repl(ip, password, cmd))
        if "WIFI_DROP" in out:
            results = _wait_for_results(base_url, auth)
    finally:
        # never leave the door controller in the REPL, also on Ctrl-C or an error
        asyncio.run(_restart_production(ip, password))

    print("\n----- results -----\n" + (results or "run.py did not finish, see console output above"))
    if "FAIL" in results or "DONE" not in results:
        sys.exit(1)
