""" Stand-alone module to calculate sunrise and sunset times. """

import math
import time as utime
from typing import Tuple, Dict, List


def getCurrentUTC() -> List[int]:
    now = utime.localtime()
    return [now[2], now[1], now[0]]


def forceRange(v: float, max_value: int) -> float:
    """Force v to be >= 0 and < max_value"""
    if v < 0:
        return v + max_value
    elif v >= max_value:
        return v - max_value
    return v


class Sun:
    """Calculate sunrise and sunset."""

    def __init__(self, latlon: Tuple[float, float]) -> None:
        self.latitude, self.longitude = latlon

    def sunrise(self) -> Dict[str, float]:
        """Calculate sunrise time."""
        return self._calcSunTime(isRiseTime=True)

    def sunset(self) -> Dict[str, float]:
        """Calculate sunset time."""
        return self._calcSunTime(isRiseTime=False)

    def _calcSunTime(self, isRiseTime: bool, zenith: float = 90.8) -> Dict[str, float]:
        """Calculate sun time (sunrise or sunset)."""
        day, month, year = getCurrentUTC()

        TO_RAD = math.pi / 180

        # Calculate day of the year
        N1 = math.floor(275 * month / 9)
        N2 = math.floor((month + 9) / 12)
        N3 = 1 + math.floor((year - 4 * math.floor(year / 4) + 2) / 3)
        N = N1 - (N2 * N3) + day - 30

        # Convert longitude to hour value and calculate approximate time
        lngHour = self.longitude / 15
        t = N + ((6 - lngHour) / 24 if isRiseTime else (18 - lngHour) / 24)

        # Calculate the Sun's mean anomaly
        M = (0.9856 * t) - 3.289

        # Calculate the Sun's true longitude
        L = (
            M
            + (1.916 * math.sin(TO_RAD * M))
            + (0.020 * math.sin(TO_RAD * 2 * M))
            + 282.634
        )
        L = forceRange(L, 360)

        # Calculate the Sun's right ascension
        RA = (1 / TO_RAD) * math.atan(0.91764 * math.tan(TO_RAD * L))
        RA = forceRange(RA, 360)

        # Adjust RA to the same quadrant as L
        Lquadrant = (math.floor(L / 90)) * 90
        RAquadrant = (math.floor(RA / 90)) * 90
        RA = RA + (Lquadrant - RAquadrant)

        # Convert RA to hours
        RA = RA / 15

        # Calculate the Sun's declination
        sinDec = 0.39782 * math.sin(TO_RAD * L)
        cosDec = math.cos(math.asin(sinDec))

        # Calculate the Sun's local hour angle
        cosH = (
            math.cos(TO_RAD * zenith) - (sinDec * math.sin(TO_RAD * self.latitude))
        ) / (cosDec * math.cos(TO_RAD * self.latitude))

        if cosH > 1:
            raise ValueError(
                "the sun never rises on this location (on the specified date)"
            )

        if cosH < -1:
            raise ValueError(
                "the sun never sets on this location (on the specified date)"
            )

        # Finish calculating H and convert into hours
        H = (
            360 - (1 / TO_RAD) * math.acos(cosH)
            if isRiseTime
            else (1 / TO_RAD) * math.acos(cosH)
        )
        H = H / 15

        # Calculate local mean time of rising/setting
        T = H + RA - (0.06571 * t) - 6.622

        # Adjust back to UTC
        UT = T - lngHour
        UT = forceRange(UT, 24)

        # Return
        hr = forceRange(int(UT), 24)
        minutes = round((UT - int(UT)) * 60, 0)

        return {"decimal": UT, "hr": hr, "min": minutes}


if __name__ == "__main__":
    from my_secrets import LOCATION_LATLON

    sun = Sun(LOCATION_LATLON)
    print(f"Sunrise: {sun.sunrise()}")
    print(f"Sunset: {sun.sunset()}")
