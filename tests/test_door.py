import pytest
from unittest.mock import MagicMock, patch


def test_open_close():
    """test open and close timing"""

    from door import Door

    door = Door(save_state=False)

    # test open and close
    door.close()

    door.open()


def test_automate():
    """Test automate function for handling different times of day."""
    from door import Door, EXTRA_DELAY

    with patch("door.Door.open", new_callable=MagicMock) as mock_open, patch(
        "door.Door.close", new_callable=MagicMock
    ) as mock_close:
        door = Door(save_state=False)

        def reset_mocks():
            mock_open.reset_mock()
            mock_close.reset_mock()

        reset_mocks()

        # Test before open time
        sleep_duration = door.automate(0, 6, 18)
        assert (
            sleep_duration == 6 * 3600 + EXTRA_DELAY
        ), "Sleep duration should be until open time"
        mock_close.assert_called_once()
        mock_open.assert_not_called()

        reset_mocks()

        # Test exactly at open time
        sleep_duration = door.automate(6, 6, 18)
        assert (
            sleep_duration == 12 * 3600 + EXTRA_DELAY
        ), "Sleep duration should be until close time"
        mock_open.assert_called_once()
        mock_close.assert_not_called()

        reset_mocks()
        # Test after open time and before close time
        sleep_duration = door.automate(7, 6, 18)
        assert (
            sleep_duration == 11 * 3600 + EXTRA_DELAY
        ), "Sleep duration should be remaining time until close time"
        mock_open.assert_called_once()
        mock_close.assert_not_called()

        reset_mocks()

        # Test exactly at close time
        sleep_duration = door.automate(18, 6, 18)
        assert (
            sleep_duration == 12 * 3600 + EXTRA_DELAY
        ), "Sleep duration should wrap around to next open time"
        mock_close.assert_called_once()
        mock_open.assert_not_called()

        reset_mocks()

        # Test after close time
        now, open, close = 19.0, 6.0, 18.0
        sleep_duration = door.automate(now, open, close)
        assert (
            sleep_duration == (24 - now + open) * 3600 + EXTRA_DELAY
        ), "Sleep duration should wrap around to next open time"
        mock_close.assert_called_once()
        mock_open.assert_not_called()


def test_day():
    """simulate automatic open and close door for a day"""
    from door import Door

    with patch("door.Door.open", new_callable=MagicMock) as mock_open, patch(
        "door.Door.close", new_callable=MagicMock
    ) as mock_close:
        door = Door(save_state=False)

        def reset_mocks():
            mock_open.reset_mock()
            mock_close.reset_mock()

        reset_mocks()

        open, close = 6.0, 18.0
        now = 0.0

        print(f"Testing day, {open=}, {close=}, {now=}")

        # Test before open time
        print(f"{now=}")
        sleep_duration = door.automate(now, open, close)

        mock_close.assert_called_once()
        mock_open.assert_not_called()

        reset_mocks()

        # open the door
        now += (sleep_duration + 1) / 3600  # simulate sleep
        print(f"{now=}")
        sleep_duration = door.automate(now, open, close)

        mock_close.assert_not_called()
        mock_open.assert_called_once()

        reset_mocks()

        # close the door in the evening
        now += sleep_duration / 3600
        print(f"{now=}")

        sleep_duration = door.automate(now, open, close)

        mock_close.assert_called_once()
        mock_open.assert_not_called()

        # next morning
        reset_mocks()
        now += sleep_duration / 3600
        now = now % 24
        print(f"{now=}")
        sleep_duration = door.automate(now, open, close)

        mock_open.assert_called_once()
        mock_close.assert_not_called()
