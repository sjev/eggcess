"""Module to calculate sunrise and sunset times from an explicit date.

Location is read from the LOCATION_LATLON environment variable,
which is expected to be a list like [lat, lon]. Works on CircuitPython.
"""

import math
import os

ZENITH: float = 90.8


def forceRange(v: float, max_value: int) -> float:
    """Force v to be >= 0 and < max_value."""
    if v < 0:
        return v + max_value
    elif v >= max_value:
        return v - max_value
    return v


def _get_location() -> tuple[float, float]:
    """Retrieve the location (lat, lon) from the LOCATION_LATLON environment variable."""
    # os.getenv("LOCATION_LATLON") already produces a correct list.
    loc = os.getenv("LOCATION_LATLON")
    if loc is None:
        raise ValueError("LOCATION_LATLON environment variable is not set")
    return float(loc[0]), float(loc[1])


def _calc_sun_time(
    isRiseTime: bool,
    year: int,
    month: int,
    day: int,
    lat: float,
    lon: float,
) -> dict[str, float]:
    """Calculate sunrise or sunset time using the given date and location."""
    TO_RAD: float = math.pi / 180

    # Calculate day of the year
    N1: float = math.floor(275 * month / 9)
    N2: float = math.floor((month + 9) / 12)
    N3: float = 1 + math.floor((year - 4 * math.floor(year / 4) + 2) / 3)
    N: float = N1 - (N2 * N3) + day - 30

    # Convert longitude to hour value and calculate approximate time
    lngHour: float = lon / 15
    t: float = N + ((6 - lngHour) / 24 if isRiseTime else (18 - lngHour) / 24)

    # Calculate the Sun's mean anomaly
    M: float = (0.9856 * t) - 3.289

    # Calculate the Sun's true longitude
    L: float = (
        M
        + (1.916 * math.sin(TO_RAD * M))
        + (0.020 * math.sin(TO_RAD * 2 * M))
        + 282.634
    )
    L = forceRange(L, 360)

    # Calculate the Sun's right ascension
    RA: float = (1 / TO_RAD) * math.atan(0.91764 * math.tan(TO_RAD * L))
    RA = forceRange(RA, 360)

    # Adjust RA to the same quadrant as L
    Lquadrant: float = (math.floor(L / 90)) * 90
    RAquadrant: float = (math.floor(RA / 90)) * 90
    RA = RA + (Lquadrant - RAquadrant)

    # Convert RA to hours
    RA = RA / 15

    # Calculate the Sun's declination
    sinDec: float = 0.39782 * math.sin(TO_RAD * L)
    cosDec: float = math.cos(math.asin(sinDec))

    # Calculate the Sun's local hour angle
    cosH: float = (math.cos(TO_RAD * ZENITH) - (sinDec * math.sin(TO_RAD * lat))) / (
        cosDec * math.cos(TO_RAD * lat)
    )

    if cosH > 1:
        raise ValueError("the sun never rises on this location (on the specified date)")
    if cosH < -1:
        raise ValueError("the sun never sets on this location (on the specified date)")

    # Finish calculating H and convert into hours
    H: float = (
        (360 - (1 / TO_RAD) * math.acos(cosH))
        if isRiseTime
        else ((1 / TO_RAD) * math.acos(cosH))
    )
    H = H / 15

    # Calculate local mean time of rising/setting
    T: float = H + RA - (0.06571 * t) - 6.622

    # Adjust back to UTC
    UT: float = T - lngHour
    UT = forceRange(UT, 24)

    hr: float = forceRange(int(UT), 24)
    minutes: float = round((UT - int(UT)) * 60, 0)

    return {"decimal": UT, "hr": hr, "min": minutes}


def sunrise(year: int, month: int, day: int) -> dict[str, float]:
    """Calculate sunrise time for the given date using location from LOCATION_LATLON."""
    lat, lon = _get_location()
    return _calc_sun_time(True, year, month, day, lat, lon)


def sunset(year: int, month: int, day: int) -> dict[str, float]:
    """Calculate sunset time for the given date using location from LOCATION_LATLON."""
    lat, lon = _get_location()
    return _calc_sun_time(False, year, month, day, lat, lon)


if __name__ == "__main__":  # pragma: no cover
    # Example usage: prints sunrise and sunset times for a given date.
    print("Sunrise:", sunrise(2023, 6, 21))
    print("Sunset:", sunset(2023, 6, 21))
