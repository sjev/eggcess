""" simple logging module """

import time

LOG_FILE = "log.txt"


def log_to_file(message, level: str = "INFO", file=LOG_FILE):
    """log a message to a file"""
    utc_time = time.localtime()
    log_str = f"{utc_time[0]-2000:02}-{utc_time[1]:02}-{utc_time[2]:02} {utc_time[3]:02}:{utc_time[4]:02}:{utc_time[5]:02} [{level}] {message}"

    print(log_str)
    with open(file, "a") as f:
        f.write(log_str + "\n")


def info(message):
    """log info message"""
    log_to_file(message, "INFO")


def warning(message):
    """log warning message"""
    log_to_file(message, "WARNING")


def error(message):
    """log error message"""
    log_to_file(message, "ERROR")


def truncate_log(file=LOG_FILE, max_lines=300, keep_lines=50):
    """Truncate the log file to keep only the last 'keep_lines' lines if it exceeds 'max_lines' lines."""
    with open(file, "r") as f:
        lines = f.readlines()

    line_count = len(lines)
    if line_count > max_lines:
        log_to_file(f"Truncating log file to {keep_lines} lines", "INFO")
        with open(file, "w") as f:
            # Keep only the last 'keep_lines' lines
            for line in lines[-keep_lines:]:
                f.write(line)
