"""simple logging module"""

import os
import time

LOG_FILE = "log.txt"


def _log_string(message: str, level: str = "INFO") -> str:
    """Return a formatted log string."""
    utc_time = time.localtime()
    return f"{utc_time[0]-2000:02}-{utc_time[1]:02}-{utc_time[2]:02} {utc_time[3]:02}:{utc_time[4]:02}:{utc_time[5]:02} [{level}] {message}"


def log_to_file(message, level: str = "INFO", file=LOG_FILE):
    """log a message to a file"""
    log_str = _log_string(message, level)

    print(log_str)
    # a full or read-only flash must never stop the door
    try:
        with open(file, "a") as f:
            f.write(log_str + "\n")
    except OSError as e:
        print(f"log write failed: {e}")


def info(message):
    """log info message"""
    log_to_file(message, "INFO")


def warning(message):
    """log warning message"""
    log_to_file(message, "WARNING")


def error(message):
    """log error message"""
    log_to_file(message, "ERROR")


def debug(message):
    """log debug message to console, not to file"""
    print(_log_string(message, "DEBUG"))


def truncate_log(file=LOG_FILE, max_lines=300, keep_lines=50):
    """Keep only the last 'keep_lines' lines once the file exceeds 'max_lines'."""
    try:
        _truncate(file, max_lines, keep_lines)
    except OSError as e:
        print(f"log truncate failed: {e}")


def _truncate(file: str, max_lines: int, keep_lines: int):
    with open(file, "r") as f:
        line_count = sum(1 for _ in f)

    if line_count <= max_lines:
        return

    print(f"Truncating log file to {keep_lines} lines")
    with open(file, "r") as fr:
        with open(file + ".tmp", "w") as fw:
            for _ in range(line_count - keep_lines):
                fr.readline()
            for line in fr:
                fw.write(line)

    os.rename(file + ".tmp", file)


# ------------ testing


def test():
    # Step 1: Create a new 'test_log.txt' with 500 lines
    with open("test_log.txt", "w") as f:
        for i in range(1, 501):
            f.write(f"Line {i}\n")

    # Step 2: Truncate the file to 20 lines
    truncate_log(file="test_log.txt", max_lines=300, keep_lines=20)

    # Step 3: Check new number of lines and Step 4: Print the lines
    with open("test_log.txt", "r") as f:
        lines = f.readlines()
        print(f"New number of lines: {len(lines)}")
        print("Remaining lines:")
        for line in lines:
            print(line, end="")  # Use end='' to avoid adding extra newlines

    # Step 5: Delete 'test_log.txt'
    os.remove("test_log.txt")
