from invoke import task
from pathlib import Path


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
