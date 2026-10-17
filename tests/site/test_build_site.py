"""生成物の公開範囲と、読書に必要なリンクを検証する。"""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('build_site', ROOT/'scripts/build_site.py')
site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site)


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='hxh-site-test-')
        cls.output = Path(cls.temp.name)/'site'
        cls.count = site.build(ROOT, cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_all_declared_pages_are_built(self):
        pages = site.load_pages(ROOT)['pages']
        self.assertEqual(self.count, len(pages))
        self.assertTrue(all((self.output/p['output']).is_file() for p in pages))

    def test_private_material_is_not_published(self):
        files = [str(p.relative_to(self.output)) for p in self.output.rglob('*') if p.is_file()]
        self.assertFalse(any(p.startswith(('design/','sources/','skills/','scripts/','.git/')) for p in files))
        self.assertFalse(any(p.endswith('.md') for p in files))
        self.assertFalse((self.output/'AGENTS.html').exists())
        for path in self.output.rglob('*.html'):
            text = path.read_text()
            self.assertNotIn('href="../design/', text)
            self.assertNotIn('href="../sources/', text)
            self.assertNotIn('対象コミット', text)

    def test_gm_scenario_is_explicitly_marked(self):
        gm = (self.output/'scenarios/01-missing-cargo-gm.html').read_text()
        self.assertIn('GM向け・ネタバレあり', gm)
        self.assertIn('class="spoiler"', gm)
        entries = json.loads((self.output/'search.json').read_text())
        matching = [x for x in entries if x['url'].endswith('-gm.html')]
        self.assertEqual(len(matching), 1)
        self.assertTrue(matching[0]['gm'])
        self.assertTrue(all(not x['url'].startswith(('design/', 'sources/')) for x in entries))

    def test_existing_anchors_and_tables_work(self):
        nen = (self.output/'rules/04-nen.html').read_text()
        self.assertIn('id="a05"', nen)
        self.assertIn('id="sec-11"', nen)
        self.assertIn('<table>', nen)
        self.assertIn('href="07-combat.html"', nen)
        self.assertIn('href="../index.html"', nen)

    def test_every_page_has_rights_notice(self):
        for path in self.output.rglob('*.html'):
            text = path.read_text()
            self.assertIn('非公式二次創作TRPG', text)
            self.assertIn('notice.html', text)
        self.assertIn('公式窓口', (self.output/'notice.html').read_text())

    def test_broken_generated_link_is_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)/'site'
            shutil.copytree(self.output, out)
            page = out/'index.html'
            page.write_text(page.read_text().replace('rules/01-introduction.html','rules/not-there.html'))
            with self.assertRaisesRegex(ValueError, 'リンク切れ'):
                site.verify_site(out)

    def test_source_allowlist_cannot_include_design_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'web').mkdir()
            config = json.loads((ROOT/'web/site.json').read_text())
            config['pages'] = [dict(source='design/verification.md',title='秘密',group='秘密')]
            (root/'web/site.json').write_text(json.dumps(config))
            with self.assertRaisesRegex(ValueError, '公開対象外'):
                site.load_pages(root)

    def test_build_does_not_overwrite_an_existing_directory(self):
        with self.assertRaisesRegex(ValueError, '空ではありません'):
            site.build(ROOT, self.output)


if __name__=='__main__':
    unittest.main()
