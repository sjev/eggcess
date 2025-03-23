import datetime
import math
import pytest
from sun import sunrise, sunset
from astral import LocationInfo
from astral.sun import sun as a_sun
from datetime import timezone

# Tolerance in decimal hours: 1 minute ~ 1/60
TOLERANCE = 1 / 60


@pytest.mark.parametrize(
    "lat,lon,test_date",
    [
        (52.37, 4.89, datetime.date(2023, 6, 21)),  # Amsterdam on June 21
        (40.7128, -74.0060, datetime.date(2023, 12, 21)),  # New York on Dec 21
    ],
)
def test_sunrise(mocker, lat: float, lon: float, test_date: datetime.date) -> None:
    # Override os.getenv to simulate a correct list being returned
    mocker.patch("os.getenv", return_value=[lat, lon])

    # Calculate sunrise using the new function interface
    result = sunrise(test_date.year, test_date.month, test_date.day)
    calculated_decimal = result["decimal"]

    # Get reference sunrise from Astral in UTC
    location = LocationInfo("Test", "Test", "UTC", lat, lon)
    s = a_sun(location.observer, date=test_date, tzinfo=timezone.utc)
    expected = s["sunrise"]
    expected_decimal = expected.hour + expected.minute / 60 + expected.second / 3600

    # Compare results within tolerance
    assert math.isclose(
        calculated_decimal, expected_decimal, abs_tol=TOLERANCE
    ), f"Sunrise: calculated {calculated_decimal}, expected {expected_decimal}"


@pytest.mark.parametrize(
    "lat,lon,test_date",
    [
        (52.37, 4.89, datetime.date(2023, 6, 21)),  # Amsterdam on June 21
        (40.7128, -74.0060, datetime.date(2023, 12, 21)),  # New York on Dec 21
    ],
)
def test_sunset(mocker, lat: float, lon: float, test_date: datetime.date) -> None:
    # Override os.getenv to simulate the correct location list
    mocker.patch("os.getenv", return_value=[lat, lon])

    # Calculate sunset using the new function interface
    result = sunset(test_date.year, test_date.month, test_date.day)
    calculated_decimal = result["decimal"]

    # Get reference sunset from Astral in UTC
    location = LocationInfo("Test", "Test", "UTC", lat, lon)
    s = a_sun(location.observer, date=test_date, tzinfo=timezone.utc)
    expected = s["sunset"]
    expected_decimal = expected.hour + expected.minute / 60 + expected.second / 3600

    # Compare results within tolerance
    assert math.isclose(
        calculated_decimal, expected_decimal, abs_tol=TOLERANCE
    ), f"Sunset: calculated {calculated_decimal}, expected {expected_decimal}"
