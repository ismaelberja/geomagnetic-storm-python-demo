import json
import re
import tempfile
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from geomag_demo.synthetic import two_time_snapshots
from geomag_demo.visuals import projection,camera_vector,globe_svg

ROOT=Path(__file__).resolve().parents[1]
FIGURES=ROOT/'figures'

class GalleryReleaseTests(unittest.TestCase):
    def test_all_eleven_svg_parse_and_render_document(self):
        files=sorted(FIGURES.glob('synthetic_*.svg'))
        self.assertEqual(len(files),11)
        for f in files:
            with self.subTest(svg=f.name):
                xml=ET.fromstring(f.read_bytes())
                self.assertEqual(xml.tag,'{http://www.w3.org/2000/svg}svg')
                self.assertTrue(xml.attrib['viewBox'])
                self.assertGreater(f.stat().st_size,3000)
                self.assertNotIn('<script',f.read_text().lower())
    def test_orthographic_coordinate_orientation(self):
        left=projection(-40,0,0)
        right=projection(40,0,0)
        self.assertLess(left[1],right[1])
        self.assertGreater(left[2],0)
        vx,vy=camera_vector(0,0,0,0,1,0)
        self.assertGreater(vx,0)  # local east points screen right at lon=0
    def test_reproducible_svg_and_html_sources(self):
        r=two_time_snapshots()['18:00']
        self.assertEqual(globe_svg(r), (FIGURES/'synthetic_zonal_globe.svg').read_text(encoding='utf-8'))
    def test_html_is_offline_self_contained_and_labelled(self):
        text=(FIGURES/'interactive_synthetic_globe.html').read_text(encoding='utf-8')
        self.assertIn('100% fictional',text)
        self.assertIn('SIM-001',text)
        self.assertIn('17:00',text)
        self.assertIn('18:00',text)
        self.assertNotRegex(text,r'(?i)\bfetch\s*\(|<iframe|<script[^>]+src=')
        self.assertNotRegex(text,r'(?i)(?:href|src)\s*=\s*["\']https?://')
    def test_readme_previews_all_figures_without_broken_links(self):
        md=(ROOT/'README.md').read_text(encoding='utf-8')
        embeds=re.findall(r'!\[[^\]]*\]\((figures/[^)]+)\)',md)
        self.assertEqual(len(embeds),11)
        self.assertEqual(len(set(embeds)),11)
        self.assertEqual(set(embeds),{f'figures/{x.name}' for x in FIGURES.glob('synthetic_*.svg')})
        for dest in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',md):
            if not re.match(r'^(?:https?://|mailto:|#)',dest):
                self.assertTrue((ROOT/dest).exists(),dest)
    def test_social_preview_has_correct_png_dimensions(self):
        import struct
        picture=(ROOT/'assets/github_social_preview.png').read_bytes()
        self.assertTrue(picture.startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertEqual(struct.unpack('>II',picture[16:24]),(1280,640))

    def test_public_package_has_no_private_thesis_assets(self):
        bad=[]
        for f in ROOT.rglob('*'):
            if not f.is_file() or '__pycache__' in f.parts or 'outputs' in f.parts:
                continue
            if f.suffix.lower() in {'.min','.pdf','.xlsx','.zip','.env'}:
                bad.append(str(f.relative_to(ROOT)))
        self.assertEqual(bad,[])
        self.assertIn('MIT License',(ROOT/'LICENSE').read_text(encoding='utf-8'))

    def test_manifest_no_real_data_and_counts(self):
        info=json.loads((FIGURES/'synthetic_manifest.json').read_text())
        self.assertIn('NO REAL INTERMAGNET',info['source'])
        self.assertEqual(info['stations_total'],56)
        self.assertEqual(info['usable_station_pairs']['17:00'],54)
        self.assertEqual(info['usable_station_pairs']['18:00'],54)

if __name__=='__main__':unittest.main()
