#!/usr/bin/env python3
"""Create local, artificial IAGA-style minute files to exercise QC; never real data."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from geomag_demo.synthetic import STATIONS,dates  # noqa: E402
from geomag_demo.analysis import synthetic_iaga_day,read_synthetic_iaga  # noqa: E402


def generate(output_root:Path) ->Path:
    output_root.mkdir(parents=True,exist_ok=True)
    target=output_root/('FICTIONAL_XYZ_'+uuid4().hex[:10])
    target.mkdir(exist_ok=False)
    for station in (STATIONS[0],STATIONS[1],STATIONS[6]):
        folder=target/station.code
        folder.mkdir()
        for day in dates():
            file=folder/f'{station.code.lower()}_{day:%Y%m%d}_synthetic.min'
            content=synthetic_iaga_day(station,day)
            result=read_synthetic_iaga(content,station.code)
            if result['missing']<0:
                raise RuntimeError('Invalid fixture')
            file.write_text(content,encoding='utf-8')
    (target/'README.txt').write_text('FICTIONAL TRAINING DATA ONLY. NOT INTERMAGNET. DO NOT CITE AS EARTH OBSERVATIONS.\n',encoding='utf-8')
    return target


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output-root',type=Path,default=ROOT/'outputs')
    args=ap.parse_args()
    print(f'Synthetic minute files created in {generate(args.output_root).resolve()}')

if __name__=='__main__':main()
