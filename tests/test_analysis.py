import math
import tempfile
from pathlib import Path
from datetime import date
import unittest
from geomag_demo.synthetic import STATIONS, BASE_DAY, EVENT_DAY, xyz, horizontal, two_time_snapshots
from geomag_demo.analysis import (read_synthetic_iaga, synthetic_iaga_day, valid_xyz, cell_id,
                                  zones_for_hour, daily_ranges, export_snapshots)

class QualityPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=synthetic_iaga_day(STATIONS[0],BASE_DAY)
    def test_parse_generated_minute_file(self):
        r=read_synthetic_iaga(self.source,STATIONS[0].code)
        self.assertEqual((r['valid'],r['missing']),(1440,0))
        self.assertEqual(r['date'],BASE_DAY)
    def test_explicit_synthetic_provenance(self):
        self.assertIn('SYNTHETIC',self.source)
        with self.assertRaisesRegex(ValueError,'refuses external'):
            read_synthetic_iaga(self.source.replace('FICTIONAL SYNTHETIC','INTERMAGNET SOURCE'))
    def test_reject_wrong_station(self):
        with self.assertRaisesRegex(ValueError,'Station'):
            read_synthetic_iaga(self.source,'SIM-999')
    def test_reject_bad_coordinate_format(self):
        with self.assertRaisesRegex(ValueError,'Expected IAGA'):
            read_synthetic_iaga(self.source.replace('IAGA-2002','IAGA-1900'))
    def test_reject_duplicate_utc_minute(self):
        data=self.source+self.source.splitlines(9)[-1]+'\n'
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            read_synthetic_iaga(data)
    def test_reject_invalid_doy(self):
        s=self.source.replace(' 130 ', ' 131 ',1)
        with self.assertRaisesRegex(ValueError,'day-of-year'):
            read_synthetic_iaga(s)
    def test_partial_and_full_day_data_gaps(self):
        miss=read_synthetic_iaga(synthetic_iaga_day(STATIONS[1],date(2024,5,13)),STATIONS[1].code)
        self.assertEqual((miss['valid'],miss['missing']),(0,1440))
        part=read_synthetic_iaga(synthetic_iaga_day(STATIONS[6],date(2024,5,11)),STATIONS[6].code)
        self.assertEqual((part['valid'],part['missing']),(1395,45))
    def test_sentinels_are_missing_not_zero(self):
        self.assertFalse(valid_xyz((99999.0,3,4)))
        self.assertFalse(valid_xyz((float('nan'),2,3)))
        self.assertTrue(valid_xyz((0.0,2,3)))
    def test_cells_keep_signed_south_latitudes(self):
        self.assertEqual(cell_id(-44,-100),(1,1))
        self.assertEqual(cell_id(44,100),(4,4))
        with self.assertRaises(ValueError):cell_id(99,0)
    def test_zones_require_two_stations(self):
        snap=two_time_snapshots()['18:00']
        regions=zones_for_hour(snap)
        self.assertEqual(len(regions),36)
        self.assertTrue(any(x['count']>=2 for x in regions))
        self.assertTrue(any(x['count']==0 for x in regions))
        self.assertTrue(all(x['median_delta_h_nt'] is None for x in regions if x['count']<2))
        with self.assertRaises(ValueError):zones_for_hour(snap,min_count=1)
    def test_duplicate_observatory_is_not_double_counted(self):
        a=two_time_snapshots()['18:00']
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            zones_for_hour(a+[a[0]])
    def test_daily_full_gap_has_none_not_interpolation(self):
        out=daily_ranges(STATIONS[1])
        self.assertEqual(len(out),7)
        self.assertIsNone(out[4]['range_h_nt'])
        self.assertEqual(out[4]['count'],0)
    def test_reference_delta_formula(self):
        r=two_time_snapshots()['18:00'][0]
        s=next(x for x in STATIONS if x.code==r['station'])
        self.assertAlmostEqual(r['delta_h_nt'],horizontal(xyz(s,EVENT_DAY,1080))-horizontal(xyz(s,BASE_DAY,1080)),places=5)
    def test_csv_no_raw_observations(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/'derived.csv'
            export_snapshots(dest,two_time_snapshots())
            s=dest.read_text(encoding='utf-8')
            self.assertIn('SIM-001',s)
            self.assertNotIn('Geodetic',s)
            self.assertNotIn('INTERMAGNET',s)
            self.assertEqual(len(s.splitlines()),1+108)

if __name__=='__main__':unittest.main()
