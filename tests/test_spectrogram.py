"""Scientific/numerical regression tests for fully synthetic STFT demonstration."""
from __future__ import annotations

import math
import unittest
import xml.etree.ElementTree as ET

from geomag_demo.spectrogram import (
    FS_HZ, HOP_MINUTES, WINDOW_MINUTES, FREQUENCIES_MHZ,
    STATION_CODES, fft_radix2, injected_trace, periodogram,
    spectrogram_svg, spectrum_for, stft,
)
from geomag_demo.synthetic import STATIONS


class SpectrogramTests(unittest.TestCase):
    def test_fft_matches_direct_dft(self):
        values = [complex(math.cos(i * 0.4), math.sin(i * 0.13)) for i in range(8)]
        fft = fft_radix2(values)
        for k in range(len(values)):
            expected = sum(z * complex(math.cos(-2 * math.pi * k * i / 8),
                                       math.sin(-2 * math.pi * k * i / 8))
                           for i, z in enumerate(values))
            self.assertAlmostEqual(fft[k].real, expected.real, places=10)
            self.assertAlmostEqual(fft[k].imag, expected.imag, places=10)

    def test_fft_rejects_bad_length(self):
        with self.assertRaises(ValueError):
            fft_radix2([1+0j] * 7)
        with self.assertRaises(ValueError):
            fft_radix2([])

    def test_known_sine_frequencies_have_correct_bins(self):
        f1, f2 = FREQUENCIES_MHZ
        self.assertAlmostEqual(f1, 2.34375)
        self.assertAlmostEqual(f2, 4.296875)
        times = range(WINDOW_MINUTES)
        signal = [14 * math.sin(2 * math.pi * (f1 / 1000) * (t*60)) +
                   5 * math.sin(2 * math.pi * (f2 / 1000) * (t*60)) for t in times]
        psd = periodogram(signal)
        peaks = sorted(range(len(psd)), key=lambda idx: psd[idx], reverse=True)
        # Hann taper spreads power to adjacent bins. The largest peak is f1.
        self.assertEqual(peaks[0] + 4, 18)
        self.assertGreater(psd[18 - 4], psd[24 - 4] * 50)
        self.assertGreater(psd[33 - 4], psd[27 - 4] * 30)

    def test_periodogram_refuses_nonfinite_input(self):
        with self.assertRaises(ValueError):
            periodogram([0.0] * 127)
        with self.assertRaises(ValueError):
            periodogram([0.0] * 127 + [float('nan')])

    def test_gap_invalidates_every_overlapping_window(self):
        signal = [0.0] * 1440
        signal[17*60:18*60+1] = [None] * 61
        report = stft(signal, 'SIM-TST')
        invalid = [m for m, powers in zip(report.centers_minute, report.columns) if powers is None]
        self.assertEqual(len(invalid), 10)
        self.assertTrue(all(m > 15*60 for m in invalid))
        self.assertTrue(all(m < 20*60 for m in invalid))
        self.assertEqual(len(report.columns), len(range(0,1440-128+1,HOP_MINUTES)))
        # No negative or zero PSD: genuine zeros are allowed for a quiet signal.
        self.assertTrue(all(all(v == 0 for v in col) for col in report.columns if col is not None))

    def test_bad_day_length_is_rejected(self):
        with self.assertRaises(ValueError):
            stft([0.0] * 100)

    def test_both_fictional_stations_have_expected_coverage(self):
        one = spectrum_for(STATIONS[0])
        twelve = spectrum_for(STATIONS[11])
        self.assertEqual((one.station, twelve.station), STATION_CODES)
        self.assertEqual(sum(c is None for c in one.columns), 0)
        self.assertEqual(sum(c is None for c in twelve.columns), 10)
        self.assertEqual(sum(c is not None for c in one.columns), 66)
        self.assertEqual(sum(c is not None for c in twelve.columns), 56)
        self.assertEqual(len(injected_trace(STATIONS[0])), 1440)

    def test_plot_is_valid_self_contained_svg_and_discloses_artificial_signals(self):
        text = spectrogram_svg()
        node = ET.fromstring(text)
        self.assertEqual(node.tag, '{http://www.w3.org/2000/svg}svg')
        for label in ('SIM-001','SIM-012','128-minute','Hann','mHz',
                      'INJECTED TEST FREQUENCIES','FICTIONAL','NO COMPLETE'):
            self.assertIn(label,text)
        self.assertNotIn('<script',text.lower())
        self.assertNotIn('INTERMAGNET observations',text)
        self.assertEqual(text, spectrogram_svg())


if __name__ == '__main__':
    unittest.main()
