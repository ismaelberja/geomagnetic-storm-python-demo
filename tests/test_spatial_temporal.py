"""Offline scientific-method regression on wholly fictional XYZ observations."""
from datetime import date
import math
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET

from geomag_demo.synthetic import STATIONS
from geomag_demo.spatial_temporal import (
    MIN_BAND_STATIONS, DAY_LIST, hourly_median, compare_station_hours,
    aggregate_bands, peak_by_latitude, spearman, ranks, heatmap_svg,
    latitude_peak_svg, render_all,
)


class GeographicTemporalMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=compare_station_hours()
        cls.lat=aggregate_bands(cls.rows,'latitude')
        cls.lon=aggregate_bands(cls.rows,'longitude')
        cls.peaks=peak_by_latitude(cls.rows)

    def test_station_count_and_UTC_grid(self):
        self.assertEqual(len(self.rows),56*6*24)
        self.assertEqual({p['station'] for p in self.rows},{s.code for s in STATIONS})
        self.assertEqual(len({(x['date'],x['hour']) for x in self.rows}),144)

    def test_real_data_never_loaded_and_synthetic_provenance(self):
        out,metadata=render_all(STATIONS[:5])
        self.assertEqual(len(out),3)
        self.assertIn('NO INTERMAGNET',metadata['source'])
        self.assertEqual(metadata['station_total'],5)

    def test_gap_is_none_not_zero(self):
        s=next(s for s in STATIONS if s.code=='SIM-012')
        self.assertIsNone(hourly_median(s,date(2024,5,10),17))
        vals=[r for r in self.rows if r['station']==s.code and r['date']==date(2024,5,10)]
        self.assertIsNone(vals[17]['delta_h_nt'])
        self.assertIsNotNone(vals[18]['delta_h_nt'])

    def test_missing_full_day_not_joined(self):
        s=next(s for s in STATIONS if s.code=='SIM-002')
        self.assertIsNone(hourly_median(s,date(2024,5,13),7))
        self.assertTrue(all(r['delta_h_nt'] is None for r in self.rows if r['station']==s.code and r['date']==date(2024,5,13)))

    def test_band_sufficiency_and_valid_medians(self):
        self.assertEqual(MIN_BAND_STATIONS,3)
        self.assertEqual(len(self.lat),6*24*6)
        self.assertEqual(len(self.lon),6*24*6)
        for r in self.lat+self.lon:
            self.assertEqual(r['median_delta_h_nt'] is None,r['n_valid_stations']<MIN_BAND_STATIONS)

    def test_bands_preserve_signed_southern_latitude(self):
        stamp=[r for r in self.lat if r['date']==date(2024,5,10) and r['hour']==10]
        self.assertEqual({r['band'] for r in stamp},set(range(6)))
        self.assertGreater(sum(r['n_valid_stations'] for r in stamp if r['band']<3),0)

    def test_duplicate_station_in_hour_rejected(self):
        same=dict(self.rows[0]);
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            aggregate_bands([same,same],'latitude')

    def test_geographical_axis_argument_checked(self):
        with self.assertRaises(ValueError):aggregate_bands(self.rows,'magnetic_latitude')
        with self.assertRaises(ValueError):aggregate_bands(self.rows,'latitude',min_stations=1)
        with self.assertRaises(ValueError):hourly_median(STATIONS[0],date(2024,5,10),24)

    def test_station_peak_selection_and_rank(self):
        self.assertEqual(len(self.peaks),56)
        self.assertTrue(all(p['n_event_hours']>=10 and p['peak_abs_delta_h_nt']>=0 for p in self.peaks))
        self.assertAlmostEqual(spearman([1,2,3],[3,2,1]),-1)
        self.assertAlmostEqual(spearman([1,2,3],[3,4,5]),1)
        self.assertIsNone(spearman([1,1,1],[1,2,3]))

    def test_svg_is_parseable_offline_and_unmistakably_synthetic(self):
        f1=heatmap_svg(self.lat,'latitude');f2=heatmap_svg(self.lon,'longitude');f3=latitude_peak_svg(self.peaks)
        for s in (f1,f2,f3):
            xml=ET.fromstring(s)
            self.assertEqual(xml.tag,'{http://www.w3.org/2000/svg}svg')
            self.assertIn('FICTIONAL',s)
            self.assertNotIn('<script',s.lower())
            self.assertNotIn('INTERMAGNET',s.replace('NOT INTERMAGNET',''))
        self.assertIn('fewer than 3 stations',f1)
        self.assertIn('Spearman',f3)


if __name__=='__main__':unittest.main()
