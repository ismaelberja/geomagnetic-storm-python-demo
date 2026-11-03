"""Synthetic, gap-aware short-time power spectrum and SVG heat map (stdlib only).

This example introduces *additional, explicitly artificial* ULF-like waves to
already fictional station H differences. It is NOT an analysis of actual 2024
observatory data; the frequencies are known injected demonstration signals.
"""
from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from statistics import mean

from .synthetic import BASE_DAY, EVENT_DAY, STATIONS, Station, horizontal, xyz
from .visuals import BG, TEXT, MUTED, CYAN, CORAL, GRID, SURFACE, txt

FS_HZ = 1.0 / 60.0  # one synthetic reading per UTC minute
WINDOW_MINUTES = 128
HOP_MINUTES = 20
LOW_BIN = 4  # >=0.52 mHz (DC and ultra-low drift suppressed)
HIGH_BIN = 61  # <=7.94 mHz, below the 8.33 mHz Nyquist frequency
FREQUENCIES_MHZ = (18 * FS_HZ / WINDOW_MINUTES * 1000,
                    33 * FS_HZ / WINDOW_MINUTES * 1000)
STATION_CODES = ('SIM-001', 'SIM-012')


@dataclass(frozen=True)
class Spectrum:
    station: str
    centers_minute: tuple[int, ...]
    frequencies_mhz: tuple[float, ...]
    # values: one frequency power row per time center; None => invalid window
    columns: tuple[tuple[float, ...] | None, ...]


def injected_trace(station: Station) -> list[float | None]:
    """Generate ΔH and injected harmonics on fictional dates only.

    The 128-min Hann spectrum visualizes oscillations explicitly added here.
    Gaps follow the common synthetic XYZ fixture (never filled).
    """
    result: list[float | None] = []
    f1, f2 = [f / 1000 for f in FREQUENCIES_MHZ]
    for minute in range(1440):
        base, event = xyz(station, BASE_DAY, minute), xyz(station, EVENT_DAY, minute)
        if base is None or event is None:
            result.append(None)
            continue
        t = minute * 60.0
        # The wave packet is strongest around a completely fictional 18:30 UTC.
        envelope = math.exp(-0.5 * ((minute - 18.5 * 60) / 100) ** 2)
        amplitude = 1.0 + 13.0 * envelope
        # Different amplitudes for the two panels, but identical frequencies.
        phase = 0.17 if station.code == 'SIM-001' else 0.49
        wave = amplitude * math.sin(2 * math.pi * f1 * t + phase)
        wave += (0.6 + 6.2 * envelope) * math.sin(2 * math.pi * f2 * t + 0.30)
        result.append(horizontal(event) - horizontal(base) + wave)
    return result


def fft_radix2(values: list[complex]) -> list[complex]:
    """Cooley-Tukey FFT, forward convention exp(-i 2πkn/N)."""
    n = len(values)
    if n < 2 or (n & (n - 1)):
        raise ValueError('FFT length must be a power of two, at least two')
    data = list(values)
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            data[i], data[j] = data[j], data[i]
    length = 2
    while length <= n:
        wlen = cmath.exp(-2j * math.pi / length)
        for start in range(0, n, length):
            w = 1 + 0j
            for i in range(length // 2):
                a = data[start + i]
                b = data[start + i + length // 2] * w
                data[start + i] = a + b
                data[start + i + length // 2] = a - b
                w *= wlen
        length *= 2
    return data


def periodogram(window: list[float]) -> tuple[float, ...]:
    """One-sided, detrended Hann PSD in (synthetic nT)^2/Hz.

    For k=1..N/2-1, PSD=2|FFT(w*x)|²/(fs*Σw²). The DC and Nyquist
    bins have no factor 2, though they are not displayed in our figure.
    """
    n = len(window)
    if n != WINDOW_MINUTES or any(not math.isfinite(v) for v in window):
        raise ValueError('Expected 128 contiguous, finite minute samples')
    avg = mean(window)
    center = (n - 1) / 2
    denom = sum((i - center) ** 2 for i in range(n))
    slope = sum((i - center) * (v - avg) for i, v in enumerate(window)) / denom
    detrended = [v - avg - slope * (i - center) for i, v in enumerate(window)]
    hann = [0.5 * (1 - math.cos(2 * math.pi * i / (n - 1))) for i in range(n)]
    result = fft_radix2([complex(v * w, 0) for v, w in zip(detrended, hann)])
    weight = sum(w * w for w in hann)
    scale = 2 / (FS_HZ * weight)
    return tuple((abs(result[k]) ** 2 * scale) for k in range(LOW_BIN, HIGH_BIN + 1))


def stft(series: list[float | None], station: str = 'SIM-001') -> Spectrum:
    if len(series) != 1440:
        raise ValueError('Full synthetic UTC day with 1,440 slots required')
    centers: list[int] = []
    columns: list[tuple[float, ...] | None] = []
    for start in range(0, len(series) - WINDOW_MINUTES + 1, HOP_MINUTES):
        chunk = series[start:start + WINDOW_MINUTES]
        centers.append(start + WINDOW_MINUTES // 2)
        # A partly missing 128-minute window is *fully unavailable*. No bridges.
        columns.append(None if any(v is None for v in chunk) else periodogram(chunk))
    frequencies = tuple(k * FS_HZ / WINDOW_MINUTES * 1000 for k in range(LOW_BIN, HIGH_BIN + 1))
    return Spectrum(station, tuple(centers), frequencies, tuple(columns))


def spectrum_for(station: Station) -> Spectrum:
    return stft(injected_trace(station), station.code)


# Dark-to-gold map; fixed display range makes two panels comparable.
COLORS = ('#172b57', '#2b64a0', '#168fa8', '#45c49a', '#c9dc69', '#ffe28b')
DISPLAY_MIN_DB = -5.0
DISPLAY_MAX_DB = 73.0


def interp_color(db: float) -> str:
    if not math.isfinite(db):
        raise ValueError('Nonfinite spectral power')
    f = min(1.0, max(0.0, (db - DISPLAY_MIN_DB) / (DISPLAY_MAX_DB - DISPLAY_MIN_DB))) * (len(COLORS) - 1)
    index = min(len(COLORS) - 2, int(f))
    part = f - index
    a = tuple(int(COLORS[index][j:j+2], 16) for j in (1, 3, 5))
    b = tuple(int(COLORS[index + 1][j:j+2], 16) for j in (1, 3, 5))
    return '#' + ''.join(f'{round(x + (y - x) * part):02x}' for x, y in zip(a, b))


def _chart_panel(spec: Spectrum, x0: int, y0: int, width: int, height: int) -> str:
    out = [f'<rect x="{x0}" y="{y0}" width="{width}" height="{height}" rx="7" fill="{SURFACE}"/>']
    n_t = len(spec.columns)
    n_f = len(spec.frequencies_mhz)
    col_width = width * HOP_MINUTES / 1440
    row_height = height / n_f
    # A column occupies its actual 20-minute UTC-centered interval.
    # Both UTC-day ends remain hatched because no full 128-minute STFT exists.
    out.append(f'<rect x="{x0}" y="{y0}" width="{width}" height="{height}" fill="url(#missingHatch)"/>')
    for i, col in enumerate(spec.columns):
        x = x0 + width * (spec.centers_minute[i] - HOP_MINUTES / 2) / 1440
        if col is None:
            out.append(f'<rect x="{x:.2f}" y="{y0}" width="{col_width+0.12:.2f}" height="{height}" fill="url(#missingHatch)"/>')
        else:
            for j, power in enumerate(col):
                db = 10 * math.log10(max(power, 1e-12))
                yy = y0 + (n_f - 1 - j) * row_height
                out.append(f'<rect x="{x:.2f}" y="{yy:.2f}" width="{col_width+0.12:.2f}" height="{row_height+0.12:.2f}" fill="{interp_color(db)}"/>')
    for hour in (0, 4, 8, 12, 16, 20, 24):
        px = x0 + hour / 24 * width
        out.append(f'<path d="M {px:.1f} {y0} v {height}" stroke="#bdd9e7" stroke-opacity=".20" stroke-width="1"/>')
        out.append(txt(px, y0 + height + 22, f'{hour:02}:00', 13, MUTED, anchor='middle'))
    bottom = spec.frequencies_mhz[0] - (spec.frequencies_mhz[1] - spec.frequencies_mhz[0]) / 2
    top = spec.frequencies_mhz[-1] + (spec.frequencies_mhz[1] - spec.frequencies_mhz[0]) / 2
    for f in (1, 2, 3, 4, 5, 6, 7):
        yy = y0 + height * (top - f) / (top - bottom)
        out.append(f'<path d="M{x0} {yy:.1f} h{width}" stroke="#bad8e5" stroke-opacity=".16"/>')
        out.append(txt(x0 - 13, yy + 5, str(f), 14, MUTED, anchor='end'))
    for f in FREQUENCIES_MHZ:
        yy = y0 + height * (top - f) / (top - bottom)
        out.append(f'<path d="M{x0} {yy:.1f} h{width}" stroke="{CORAL}" stroke-opacity=".44" stroke-dasharray="5 6"/>')
    out.append(f'<rect x="{x0}" y="{y0}" width="{width}" height="{height}" rx="7" fill="none" stroke="#46657b" stroke-width="1.6"/>')
    return ''.join(out)


def spectrogram_svg() -> str:
    """Two matched PSD panels, with explicit invalid-window hatching."""
    a, b = [spectrum_for(next(s for s in STATIONS if s.code == code)) for code in STATION_CODES]
    width, height = 1450, 965
    x0, plot_w, plot_h = 135, 1135, 260
    panels = [(a, 214), (b, 573)]
    out = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Fully synthetic, gap-aware geomagnetic H spectrograms for two fictional stations">
<title>Simulated H spectrogram, not actual geomagnetic observations</title>
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#112f44"/><stop offset="1" stop-color="{BG}"/></linearGradient>
<pattern id="missingHatch" width="12" height="12" patternUnits="userSpaceOnUse"><rect width="12" height="12" fill="#1b2935"/><path d="M-3 3 L3 -3 M0 12 L12 0 M9 15 L15 9" stroke="#6e8595" stroke-width="2" opacity=".60"/></pattern></defs>
<rect width="{width}" height="{height}" fill="url(#bg)"/>
''']
    out.extend([
        txt(60, 49, 'SCIENTIFIC PYTHON  /  100% FICTIONAL WAVE-FORM DEMO', 14, CYAN, 700, extra='letter-spacing="1.8"'),
        txt(60, 100, 'Spectrogram — artificial ΔH and wave packets', 34, TEXT, 700),
        txt(60, 138, '128-minute Hann STFT · 20-minute hop · power spectrum in mHz · no interpolation of gaps', 17, MUTED),
    ])
    for spec, top in panels:
        valid = sum(x is not None for x in spec.columns)
        text = 'complete fictional readings' if spec.station == 'SIM-001' else 'synthetic 17:00–18:00 UTC outage'
        out.append(txt(x0, top - 24, f'{spec.station}   /   {text}   /   {valid} of {len(spec.columns)} complete windows', 18, TEXT, 650))
        out.append(_chart_panel(spec, x0, top, plot_w, plot_h))
        out.append(txt(x0 - 82, top + plot_h/2, 'Frequency (mHz)', 15, MUTED, anchor='middle', extra=f'transform="rotate(-90 {x0-82:.1f} {top + plot_h/2:.1f})"'))
    out.append(txt(x0 + plot_w/2, 865, 'UTC clock time on simulated 10 May 2024', 16, MUTED, anchor='middle'))
    # Legend and clear physical/statistical limitations.
    bar_x, bar_y, bar_w, bar_h = 1292, 235, 24, 574
    for i in range(100):
        y = bar_y + (99-i)*bar_h/100
        val = DISPLAY_MIN_DB + (DISPLAY_MAX_DB - DISPLAY_MIN_DB)*i/99
        out.append(f'<rect x="{bar_x}" y="{y:.2f}" width="{bar_w}" height="{bar_h/100+.3:.2f}" fill="{interp_color(val)}"/>')
    for val in (-5, 15, 35, 55, 73):
        y = bar_y + bar_h * (DISPLAY_MAX_DB - val)/(DISPLAY_MAX_DB-DISPLAY_MIN_DB)
        out.append(txt(bar_x+36, y+4, f'{val}', 13, MUTED))
    out.extend([
        txt(1340, 190, 'PSD', 15, TEXT, 700, anchor='middle'),
        txt(1340, 210, 'dB', 14, MUTED, anchor='middle'),
        txt(60, 906, f'INJECTED TEST FREQUENCIES:  {FREQUENCIES_MHZ[0]:.2f} and {FREQUENCIES_MHZ[1]:.2f} mHz   ·   GREY HATCH = NO COMPLETE 128-min WINDOW', 15, CYAN, 650),
        txt(60, 938, 'All oscillations and the event-like step are generated mathematically. Power is dB relative to 1 nT²/Hz; not an INTERMAGNET result.', 14, MUTED),
        '</svg>'
    ])
    return ''.join(out)
