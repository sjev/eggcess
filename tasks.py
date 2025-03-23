import os
import sys
from pathlib import Path
from fnmatch import fnmatch
from click import prompt
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
