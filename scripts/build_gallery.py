#!/usr/bin/env python3
"""Rebuild every chart and offline HTML viewer from fully synthetic equations.

Usage: python scripts/build_gallery.py --output-root figures
Requires Python 3.11+ stdlib only; no observations, downloads or credentials.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from geomag_demo.synthetic import STATIONS, two_time_snapshots  # noqa: E402
from geomag_demo.analysis import export_snapshots, zones_for_hour  # noqa: E402
from geomag_demo.visuals import (band_plot, build_html, coverage_plot, daily_plot,
                                 globe_svg, line_chart)  # noqa: E402
from geomag_demo.spectrogram import spectrogram_svg, FREQUENCIES_MHZ  # noqa: E402
from geomag_demo.spatial_temporal import render_all as render_spatial_temporal  # noqa: E402
from geomag_demo.thesis_geography import render_all as render_thesis_geography  # noqa: E402


def build(root: Path) -> dict:
    root.mkdir(parents=True,exist_ok=True)
    snap=two_time_snapshots()
    outputs={
        'synthetic_zonal_globe.svg':globe_svg(snap['18:00'],'zones'),
        'synthetic_vector_globe.svg':globe_svg(snap['18:00'],'vectors'),
        'synthetic_latitude_bands.svg':band_plot(snap,'latitude'),
        'synthetic_longitude_bands.svg':band_plot(snap,'longitude'),
        'synthetic_time_series.svg':line_chart(),
        'synthetic_daily_ranges.svg':daily_plot(),
        'synthetic_coverage.svg':coverage_plot(),
        'synthetic_spectrogram.svg':spectrogram_svg(),
        'interactive_synthetic_globe.html':build_html(snap),
    }
    spatial_figures, spatial_summary = render_spatial_temporal()
    outputs.update(spatial_figures)
    thesis_figures, thesis_summary = render_thesis_geography()
    outputs.update(thesis_figures)
    for name,content in outputs.items():
        (root/name).write_text(content,encoding='utf-8',newline='\n')
    export_snapshots(root/'synthetic_station_snapshots.csv',snap)
    summaries={
        'source':'FICTIONAL SYNTHETIC DEMO; NO REAL INTERMAGNET DATA',
        'stations_total':len(STATIONS),
        'utc_times':['17:00','18:00'],
        'usable_station_pairs':{t:len(rows) for t,rows in snap.items()},
        'cells_with_two_or_more_stations':{
            t:sum(r['count']>=2 for r in zones_for_hour(rows)) for t,rows in snap.items()},
        'cell_colours_describe':'median ΔH at geographically sampled fictional stations, not a global physical field',
        'quality':'Synthetic missing observations are excluded; no interpolation',
        'spectrogram':{'status':'FULLY SYNTHETIC, additionally injected oscillations; not real field observations',
                       'stations':['SIM-001','SIM-012'], 'fft_size_minutes':128, 'hop_minutes':20,
                       'frequencies_mhz':[round(x,6) for x in FREQUENCIES_MHZ],
                       'invalid_stft_windows_in_SIM_012':10},
        'spatiotemporal':spatial_summary,
        'thesis_geographic_components':thesis_summary,
        'files':list(outputs),
    }
    (root/'synthetic_manifest.json').write_text(json.dumps(summaries,indent=2)+'\n',encoding='utf-8')
    return summaries


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output-root',type=Path,default=ROOT/'figures')
    args=ap.parse_args()
    info=build(args.output_root)
    print(f"Generated {len(info['files'])} reproducible visuals from {info['stations_total']} fictional stations: {args.output_root}")

if __name__=='__main__':main()
