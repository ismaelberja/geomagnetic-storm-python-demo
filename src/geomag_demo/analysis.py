"""Synthetic IAGA-style parser, missing-data safety and regional summaries."""
from __future__ import annotations

import csv
from datetime import date, datetime
import io
import math
from pathlib import Path
import re
from statistics import median
from .synthetic import Station, SENTINEL, dates, xyz, horizontal

DATE_ROW = re.compile(r'^\d{4}-\d{2}-\d{2}\s+')
DATA_FIELDS = ('station', 'latitude_deg', 'longitude_deg', 'time_utc', 'delta_x_nt',
               'delta_y_nt', 'delta_z_nt', 'delta_h_nt', 'delta_b_nt')


def valid_xyz(values: tuple[float,...]) -> bool:
    return len(values) == 3 and all(math.isfinite(v) and abs(v) < 99000 for v in values)


def synthetic_iaga_day(station: Station, day: date) -> str:
    """Fully synthetic minute-level IAGA-2002-shaped *training* file."""
    header = (
        f' Format                 IAGA-2002                                    |\n'
        f' Source of Data         FICTIONAL SYNTHETIC DATA - NO INTERMAGNET     |\n'
        f' Station Name           Invented simulated training station          |\n'
        f' IAGA Code              {station.code}                              |\n'
        f' Reported               XYZF                                         |\n'
        f' Data Type              SYNTHETIC - NOT CALIBRATED                  |\n'
        f' Geodetic Latitude      {station.latitude:.4f}                                   |\n'
        f' Geodetic Longitude     {station.longitude:.4f}                                   |\n'
        f'DATE       TIME         DOY      X(nT)    Y(nT)    Z(nT)    F(nT)    |\n'
    )
    out = io.StringIO()
    out.write(header)
    for minute in range(1440):
        values = xyz(station, day, minute)
        if values is None:
            x = y = z = f = SENTINEL
        else:
            x,y,z = values
            f = math.hypot(horizontal(values),z)
        out.write(f'{day.isoformat()} {minute//60:02}:{minute%60:02}:00.000 '
                  f'{day.timetuple().tm_yday:03d} {x:11.3f} {y:11.3f} {z:11.3f} {f:11.3f}\n')
    return out.getvalue()


def read_synthetic_iaga(content: str, expected_code: str | None = None) -> dict:
    """Parse own synthetic IAGA-style text; refuse real source files by policy."""
    meta: dict[str,str] = {}
    records: list[dict] = []
    seen: set[str] = set()
    last_day = None
    for line in content.splitlines():
        if DATE_ROW.match(line):
            parts = line.split()
            if len(parts) < 7:
                raise ValueError('Malformed minute row')
            try:
                stamp = datetime.fromisoformat(parts[0]+'T'+parts[1])
                doy = int(parts[2])
            except ValueError as exc:
                raise ValueError('Malformed timestamp or day') from exc
            if stamp.second or stamp.microsecond or doy != stamp.timetuple().tm_yday:
                raise ValueError('Non-minute UTC data or bad day-of-year')
            if last_day is None:
                last_day = stamp.date()
            if stamp.date() != last_day:
                raise ValueError('Mixed UTC days in single file')
            key = stamp.isoformat()
            if key in seen:
                raise ValueError('Duplicate UTC minute')
            seen.add(key)
            try:
                numbers = tuple(float(p) for p in parts[3:6])
            except ValueError:
                numbers = ()
            values = numbers if valid_xyz(numbers) else None
            records.append({'timestamp':stamp, 'xyz':values,
                            'H':horizontal(values) if values else None})
        elif '|' in line and not line.startswith('DATE'):
            name = line[:24].strip()
            if name:
                meta[name] = line[24:].split('|',1)[0].strip()
    if meta.get('Format') != 'IAGA-2002' or meta.get('Reported') != 'XYZF':
        raise ValueError('Expected IAGA-2002 XYZF')
    if not meta.get('Source of Data','').startswith('FICTIONAL SYNTHETIC'):
        raise ValueError('This public demo refuses external or real station observations')
    if meta.get('Data Type') != 'SYNTHETIC - NOT CALIBRATED':
        raise ValueError('Expected explicit synthetic provenance')
    if expected_code and meta.get('IAGA Code') != expected_code:
        raise ValueError('Station does not match expected synthetic code')
    if len(records) > 1440 or not records:
        raise ValueError('Invalid number of minute records')
    return dict(metadata=meta,records=records,valid=sum(r['H'] is not None for r in records),
                missing=1440-sum(r['H'] is not None for r in records), date=last_day)


def cell_id(lat: float, lon: float) -> tuple[int,int]:
    """Six 30° bands from -90 to 90, six 60° bands from -180 to 180."""
    if not all(math.isfinite(v) for v in (lat,lon)) or not -90<=lat<=90 or not -180<=lon<=180:
        raise ValueError('Geographic coordinate outside signed range')
    return min(5,int((lat+90)//30)), min(5,int((lon+180)//60))


def zones_for_hour(rows: list[dict], min_count: int=2) -> list[dict]:
    if min_count < 2:
        raise ValueError('At least two independent stations required per coloured cell')
    found = {}
    unique = set()
    for row in rows:
        station = str(row['station'])
        if station in unique:
            raise ValueError('Duplicate station in a UTC snapshot')
        unique.add(station)
        key = cell_id(float(row['latitude_deg']),float(row['longitude_deg']))
        value = float(row['delta_h_nt'])
        if not math.isfinite(value):
            continue
        found.setdefault(key,[]).append(value)
    result=[]
    for lat_i in range(6):
        for lon_i in range(6):
            values=found.get((lat_i,lon_i),[])
            result.append({'lat_band':lat_i,'lon_band':lon_i,'count':len(values),
                'median_delta_h_nt':median(values) if len(values)>=min_count else None})
    return result


def daily_ranges(station: Station) -> list[dict]:
    """A complete synthetic day with no valid minutes returns None, not zero."""
    out=[]
    for day in dates():
        vals=[horizontal(a) for minute in range(1440) if (a:=xyz(station,day,minute)) is not None]
        out.append({'station':station.code,'date':day.isoformat(),'count':len(vals),
                    'range_h_nt':max(vals)-min(vals) if vals else None})
    return out


def export_snapshots(path: Path, snapshots: dict[str,list[dict]]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=DATA_FIELDS)
        w.writeheader()
        for clock in ('17:00','18:00'):
            for r in snapshots[clock]:
                w.writerow({k: f'{v:.5f}' if isinstance(v,float) else v for k,v in r.items()})
