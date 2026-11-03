import math
import unittest
from datetime import date
from geomag_demo.synthetic import (STATIONS, BASE_DAY, EVENT_DAY, artificial_gap,
                                   day_effect, make_stations, sample_difference, xyz, two_time_snapshots)

class SyntheticDataTests(unittest.TestCase):
    def test_stations_are_deterministic_and_fictitious(self):
        self.assertEqual(STATIONS, make_stations())
        self.assertEqual(len(STATIONS),56)
        self.assertTrue(all(s.code.startswith('SIM-') for s in STATIONS))
        self.assertEqual(len({s.code for s in STATIONS}),56)
    def test_both_geographic_hemispheres(self):
        self.assertTrue(any(s.latitude<0 for s in STATIONS))
        self.assertTrue(any(s.latitude>0 for s in STATIONS))
        self.assertTrue(all(-90<=s.latitude<=90 and -180<=s.longitude<=180 for s in STATIONS))
    def test_snapshot_has_missing_values_not_false_zeros(self):
        s=two_time_snapshots()
        self.assertEqual(len(s['17:00']),54)
        self.assertEqual(len(s['18:00']),54)
        self.assertNotIn('SIM-012',{x['station'] for x in s['18:00']})
        self.assertNotIn('SIM-037',{x['station'] for x in s['18:00']})
    def test_artificial_full_day_gap(self):
        self.assertTrue(all(artificial_gap(STATIONS[1],date(2024,5,13),m) for m in range(1440)))
    def test_partial_gap(self):
        self.assertTrue(artificial_gap(STATIONS[6],date(2024,5,11),12*60))
        self.assertFalse(artificial_gap(STATIONS[6],date(2024,5,11),13*60))
    def test_reference_day_has_zero_artificial_effect(self):
        self.assertEqual(day_effect(BASE_DAY,18*60),0)
        self.assertGreater(day_effect(EVENT_DAY,18*60),day_effect(EVENT_DAY,17*60))
    def test_arithmetic_and_vector_magnitude(self):
        p=sample_difference(STATIONS[0],18*60)
        self.assertIsNotNone(p)
        self.assertAlmostEqual(math.sqrt(p['delta_x_nt']**2+p['delta_y_nt']**2+p['delta_z_nt']**2),p['delta_b_nt'],places=5)
        self.assertTrue(math.isfinite(p['delta_h_nt']))
    def test_no_randomness(self):
        self.assertEqual(xyz(STATIONS[0],EVENT_DAY,1030),xyz(STATIONS[0],EVENT_DAY,1030))
    def test_reject_unsupported_dates_and_times(self):
        with self.assertRaises(ValueError):xyz(STATIONS[0],date(2025,5,10),10)
        with self.assertRaises(ValueError):xyz(STATIONS[0],EVENT_DAY,1500)
    def test_station_count_range(self):
        with self.assertRaises(ValueError):make_stations(1)

if __name__=='__main__':unittest.main()
