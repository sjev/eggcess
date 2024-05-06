import os
import sys
from pathlib import Path
from fnmatch import fnmatch

import requests
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
def push(ctx, src="src/", dest="/"):
    """
    Push files from the local 'src' directory to the device, ignoring hidden files and .syncignore patterns.
    """
    secrets = get_secrets()
    base_url = f"http://{secrets['DEVICE_IP']}/fs/"
    auth = ("", secrets["DEVICE_PASS"])
    ignore_patterns = read_syncignore()

    for root, dirs, files in os.walk(src):
        files = [
            f
            for f in files
            if not f.startswith(".")
            and all(not fnmatch(f, pat) for pat in ignore_patterns)
        ]
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, src)
            device_path = f"{dest}{relative_path}".replace(
                "\\", "/"
            )  # Ensure correct path separators
            with open(local_path, "rb") as file:
                # Read the whole file content and send as raw binary data
                file_content = file.read()
                headers = {
                    "Content-Type": "application/octet-stream"
                }  # Set the content-type if necessary
                response = requests.put(
                    f"{base_url}{device_path}",
                    data=file_content,
                    auth=auth,
                    headers=headers,
                )
                print(
                    f"Uploading {local_path} to {device_path}: {response.status_code}"
                )


@task
def pull(ctx, dest="src/", src="/"):
    """
    Pull files from the device to the local 'dest' directory, ignoring hidden files and .syncignore patterns.
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
