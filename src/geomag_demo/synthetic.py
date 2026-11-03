"""Deterministic fictional observatories and XYZ values (NOT INTERMAGNET).

These functions are artificial mathematical demonstrations, not a field model.
Coordinates are invented and station identifiers are not real IAGA station IDs.
X points geographic north, Y east, Z down, expressed in illustrative nT.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import math

BASE_DAY = date(2024, 5, 9)
EVENT_DAY = date(2024, 5, 10)
END_DAY = date(2024, 5, 15)
SENTINEL = 99999.0


@dataclass(frozen=True)
class Station:
    code: str
    latitude: float
    longitude: float


def make_stations(count: int = 56) -> tuple[Station, ...]:
    """A repeatable set of fictional geographic points, not real stations."""
    if not 3 <= count <= 999:
        raise ValueError('Expected 3..999 simulated stations')
    stations = []
    for i in range(count):
        # A golden-angle distribution prevents a misleading dense Europe-only sample.
        u = -0.88 + 1.76 * (i + .5) / count
        lat = math.degrees(math.asin(u))
        lon = ((i * 137.50776405 + 23.0 + 180) % 360) - 180
        stations.append(Station(f'SIM-{i + 1:03}', round(lat, 4), round(lon, 4)))
    return tuple(stations)


STATIONS = make_stations()


def day_effect(day: date, minute: int) -> float:
    """Artificial storm-like perturbation; do not interpret as May 2024 data."""
    if not 0 <= minute < 1440:
        raise ValueError('Minute must be 0..1439')
    if day == EVENT_DAY:
        # A quick but finite transition beginning 16:45 UTC.
        delta = max(0, minute - (16 * 60 + 45))
        return (1.0 - math.exp(-delta / 24.0)) if delta else 0.0
    if day == date(2024, 5, 11):
        return .55 * math.exp(-minute / 1700.0)
    if day == date(2024, 5, 12):
        return .22 * math.exp(-minute / 900.0)
    if day > date(2024, 5, 12):
        return .03
    return 0.0


def artificial_gap(station: Station, day: date, minute: int) -> bool:
    """Deliberate missing values, including a whole-day gap and minute gaps."""
    if station.code == 'SIM-002' and day == date(2024, 5, 13):
        return True  # Complete-day outage for daily-range plotting QC.
    if station.code == 'SIM-007' and day == date(2024, 5, 11) and 12*60 <= minute < 12*60+45:
        return True
    if station.code == 'SIM-012' and day == EVENT_DAY and 17*60 <= minute <= 18*60:
        return True
    if station.code == 'SIM-037' and day == EVENT_DAY and 17*60 <= minute <= 18*60:
        return True
    return False


def xyz(station: Station, day: date, minute: int) -> tuple[float, float, float] | None:
    """Return artificial north/east/down components or None for a real gap."""
    if not BASE_DAY <= day <= END_DAY:
        raise ValueError('Synthetic demonstration is defined for 9–15 May 2024')
    if not 0 <= minute < 1440:
        raise ValueError('Minute must be 0..1439')
    if artificial_gap(station, day, minute):
        return None
    lat, lon = map(math.radians, (station.latitude, station.longitude))
    phase = 2 * math.pi * minute / 1440
    # Units and amplitudes are illustrative only; not calibrated to Earth physics.
    base_x = 22500 + 1450 * math.cos(lat) + 370 * math.sin(lon)
    base_y = 1550 + 420 * math.cos(lat) * math.sin(lon)
    base_z = 41700 + 2500 * math.sin(lat) + 380 * math.cos(lon)
    wave = 8.0 * math.sin(phase + lon / 4) + 3.0 * math.cos(3 * phase)
    d = (day - BASE_DAY).days
    natural_drift = .7 * d
    shift = day_effect(day, minute)
    magnitude = (68 + 118 * abs(math.sin(lat)) + 38 * math.cos(lon - .35)) * shift
    x = base_x + wave + natural_drift - magnitude * (0.35 + 0.90 * math.cos(lon - 0.35))
    y = base_y + 4 * math.sin(phase * 2 + lat) + .31 * magnitude * math.sin(lon)
    z = base_z + 5 * math.cos(phase + lat / 2) - .24 * magnitude * math.sin(lat)
    return x, y, z


def horizontal(values: tuple[float, float, float]) -> float:
    return math.hypot(values[0], values[1])


def sample_difference(station: Station, minute: int) -> dict[str, float | str] | None:
    a = xyz(station, BASE_DAY, minute)
    b = xyz(station, EVENT_DAY, minute)
    if a is None or b is None:
        return None
    return {
        'station': station.code,
        'latitude_deg': station.latitude,
        'longitude_deg': station.longitude,
        'time_utc': f'{minute//60:02}:{minute%60:02}',
        'delta_x_nt': round(b[0]-a[0],6),
        'delta_y_nt': round(b[1]-a[1],6),
        'delta_z_nt': round(b[2]-a[2],6),
        'delta_h_nt': round(horizontal(b)-horizontal(a),6),
        'delta_b_nt': round(math.sqrt(sum((bi-ai)**2 for ai,bi in zip(a,b))),6),
    }


def two_time_snapshots() -> dict[str, list[dict]]:
    return {
        clock: [v for station in STATIONS if (v:=sample_difference(station, minute)) is not None]
        for clock,minute in [('17:00',17*60),('18:00',18*60)]
    }


def dates() -> tuple[date, ...]:
    return tuple(BASE_DAY + timedelta(days=n) for n in range((END_DAY-BASE_DAY).days+1))
