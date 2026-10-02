import logger


def test_log_to_unwritable_file_does_not_raise(tmp_path):
    logger.log_to_file("hello", file=str(tmp_path / "missing_dir" / "log.txt"))


def test_truncate_keeps_last_lines(tmp_path):
    log = tmp_path / "log.txt"
    log.write_text("".join(f"line {i}\n" for i in range(10)))

    logger.truncate_log(file=str(log), max_lines=5, keep_lines=2)

    assert log.read_text() == "line 8\nline 9\n"


def test_truncate_missing_file_does_not_raise(tmp_path):
    logger.truncate_log(file=str(tmp_path / "missing.txt"))
