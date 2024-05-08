""" simple logging module """

import os
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
    # Check current line count in the file
    line_count = 0
    with open(file, "r") as f:
        for _ in f:
            line_count += 1

    # Only proceed if the line count exceeds the max allowed lines
    if line_count > max_lines:
        print(
            f"Truncating log file to {keep_lines} lines"
        )  # Assuming log_to_file is a print for simplicity

        # Identify the start line of the 'keep_lines' to keep
        start_line = line_count - keep_lines

        # Write the remaining lines back to the file
        with open(file, "r") as fr:
            with open(file + ".tmp", "w") as fw:
                # Skip the first 'start_line' lines
                for _ in range(start_line):
                    fr.readline()

                # Copy remaining lines one by one
                for line in fr:
                    fw.write(line)

        # Replace old file with new file
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
