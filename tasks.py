import os
import sys
from pathlib import Path

import requests
from invoke import task


def get_secrets() -> dict[str, str]:
    """get secrets from environment variables"""

    keys = ["DEVICE_IP", "DEVICE_PASS"]
    secrets = {key: os.getenv(key) for key in keys}
    print(secrets)

    # check that all secrets are present
    for k, v in secrets.items():
        if v is None:
            sys.exit(f"Error: Missing secret for {k}")

    return {k: v for k, v in secrets.items() if k is not None and v is not None}


@task
def push(ctx, src="src/", dest="/"):
    """
    Push files from the local 'src' directory to the device.
    """
    secrets = get_secrets()
    base_url = f"http://{secrets['DEVICE_IP']}/fs/"
    auth = ("", secrets["DEVICE_PASS"])

    import os

    for root, dirs, files in os.walk(src):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, src)
            device_path = f"{dest}{relative_path}"
            with open(local_path, "rb") as file:
                files = {"file": (filename, file)}
                response = requests.put(
                    f"{base_url}{device_path}", files=files, auth=auth
                )
                print(
                    f"Uploading {local_path} to {device_path}: {response.status_code}"
                )


@task
def pull(ctx, dest="src/", src="/"):
    """
    Pull files from the device to the local 'dest' directory.
    """
    secrets = get_secrets()
    base_url = f"http://{secrets['DEVICE_IP']}/fs/"
    auth = ("", secrets["DEVICE_PASS"])

    response = requests.get(
        f"{base_url}{src}", auth=auth, headers={"Accept": "application/json"}
    )
    if response.status_code == 200:
        dir_info = response.json()
        if "files" in dir_info:
            for file_info in dir_info["files"]:
                if not file_info["directory"]:  # Download only files, not directories
                    device_path = f"{src}{file_info['name']}"
                    local_path = os.path.join(dest, file_info["name"])
                    response = requests.get(f"{base_url}{device_path}", auth=auth)
                    if response.status_code == 200:
                        os.makedirs(os.path.dirname(local_path), exist_ok=True)
                        with open(local_path, "wb") as file:
                            file.write(response.content)
                        print(f"Downloaded {device_path} to {local_path}")


@task
def upload_lut(ctx):
    """
    Upload the 'sun_lut.csv' file using the CircuitPython web workflow API.
    """
    secrets = get_secrets()
    base_url = f"http://{secrets['DEVICE_IP']}/fs/"
    auth = ("", secrets["DEVICE_PASS"])
    file_path = Path("calculations/sun_lut.csv")

    # Check if file exists
    assert file_path.exists(), f"File {file_path} does not exist"
    print(f"Uploading {file_path}...")

    # Open the file and send it to the device
    with file_path.open("rb") as file:
        files = {"file": ("sun_lut.csv", file, "text/csv")}
        device_path = "lib/sun_lut.csv"  # Specify the destination path on the device
        response = requests.put(f"{base_url}{device_path}", files=files, auth=auth)

        # Check response status
        if response.status_code in [200, 201]:
            print("File uploaded successfully.")
        else:
            raise Exception(
                f"Failed to upload file: {response.status_code} {response.reason}"
            )

    print("Done")
