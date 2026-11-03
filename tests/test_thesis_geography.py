"""Regression tests for the user-authored synthetic methods missing from TFG coverage."""
from datetime import date
import unittest
from xml.etree import ElementTree as ET
from geomag_demo.synthetic import STATIONS,Station
from geomag_demo.thesis_geography import (render_all,synthetic_component_peaks,fictional_elevation,
    difference_at_peak,angular_diff_deg,declination_by_hour,component_latitude_svg)

class ThesisGeographyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.figures,cls.meta=render_all()
    def test_fully_synthetic_and_complete(self):
        self.assertEqual(len(self.figures),3)
        self.assertIn('FICTIONAL',self.meta['source'])
        self.assertEqual(self.meta['stations'],56)
    def test_signed_peak_correct_and_gap_rejection(self):
        self.assertEqual(difference_at_peak([10,5,15],11),-6)
        self.assertEqual(difference_at_peak([10,23,11],11),12)
        with self.assertRaises(ValueError):difference_at_peak([],1)
    def test_components_and_hemispheres(self):
        peaks=synthetic_component_peaks()
        self.assertEqual(len(peaks),56)
        self.assertTrue(any(x['latitude_deg']<0 for x in peaks))
        self.assertTrue(any(x['latitude_deg']>0 for x in peaks))
        self.assertTrue(all(k in peaks[0] for k in ['peak_abs_H','peak_abs_X','peak_abs_Y','peak_abs_Z']))
        self.assertTrue(all(x['n_reference']>=1200 for x in peaks))
    def test_elevation_explicitly_invented_and_missing(self):
        self.assertIsNone(fictional_elevation(STATIONS[8]))
        self.assertIsNotNone(fictional_elevation(STATIONS[0]))
        with self.assertRaises(ValueError):fictional_elevation(Station('EBR',41,0))
        self.assertEqual(self.meta['invented_elevation_available']+self.meta['invented_elevation_missing'],56)
    def test_circular_angle_wrap_is_not_358_degrees(self):
        self.assertAlmostEqual(angular_diff_deg(-179,179),2)
        self.assertAlmostEqual(angular_diff_deg(179,-179),-2)
    def test_declination_requires_independent_stations(self):
        data=declination_by_hour()
        self.assertIn((1,10),data)
        self.assertTrue(all(v['count']>=3 for v in data.values() if v['median_delta_d_deg'] is not None))
    def test_svg_is_offline_and_readable(self):
        for name,svg in self.figures.items():
            self.assertTrue(name.startswith('synthetic_'))
            self.assertEqual(ET.fromstring(svg).tag,'{http://www.w3.org/2000/svg}svg')
            self.assertIn('SYNTHETIC',svg)
            self.assertNotIn('<script',svg)
            self.assertNotIn('<foreignObject',svg)
    def test_deterministic(self):
        o,_=render_all();self.assertEqual(o,self.figures)

if __name__=='__main__': unittest.main()
