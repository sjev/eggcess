import pytest


def test_open_close():
    """test open and close timing"""

    from door import Door

    door = Door(save_state=False)
