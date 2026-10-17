"""実際のMarkdownを一時コピーで変更し、検証の外部的な成否を確認する。"""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('rulebook_validate', ROOT / 'scripts/validate.py')
validate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='hxh-validation-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(
            '.git', '.agents', '.codex', '.aws', '__pycache__'))

    def edit(self, name, before, after):
        path = self.root / name
        text = path.read_text(encoding='utf-8')
        self.assertIn(before, text)
        path.write_text(text.replace(before, after, 1), encoding='utf-8')

    def errors(self):
        return '\n'.join(validate.Validator(self.root).run())

    def test_repository_is_valid(self):
        self.assertEqual(self.errors(), '')

    def test_source_bytes_are_immutable(self):
        path = self.root / 'sources/ver-0.2.md'
        path.write_bytes(path.read_bytes().replace(b'2D6', b'3D6', 1))
        self.assertIn('SHA-256', self.errors())

    def test_revised_prose_need_not_match_original(self):
        self.edit('rules/01-introduction.md', '本作は、', 'この改訂草案は、')
        self.assertEqual(self.errors(), '')

    def test_missing_mapping_is_detected(self):
        path = self.root / 'design/source-map.md'
        text = path.read_text()
        path.write_text('\n'.join(line for line in text.splitlines() if not line.startswith('| 55 |')) + '\n')
        self.assertIn('原文対応表', self.errors())

    def test_empty_mapped_section_is_detected(self):
        self.edit('rules/04-nen.md',
                  '**最大オーラ＝10＋精神×3**\n\n現在オーラは、その時点で自由に使用できるオーラ。\n\n拘束オーラは、持続型の発などを維持するため一時的に使用不能となっているオーラ。', '')
        self.assertIn('本文が空', self.errors())

    def test_broken_link_is_detected(self):
        self.edit('README.md', 'rules/01-introduction.md', 'rules/missing.md')
        self.assertIn('リンク先なし', self.errors())

    def test_broken_anchor_is_detected(self):
        self.edit('design/source-map.md', '#sec-1)', '#missing)')
        self.assertIn('アンカー', self.errors())

    def test_same_file_fragment_is_allowed(self):
        path = self.root / 'README.md'
        path.write_text(path.read_text() + '\n<a id="local"></a>\n\n[同じページ](#local)\n')
        self.assertEqual(self.errors(), '')

    def test_hidden_directories_are_ignored(self):
        for name in ('.git', '.cache', '.agents'):
            path = self.root / name
            path.mkdir(exist_ok=True)
            (path / 'broken.md').write_text('[missing](no-file.md)')
        self.assertEqual(self.errors(), '')

    def test_duplicate_supplement_is_detected(self):
        path = self.root / 'design/supplements.md'
        line = next(x for x in path.read_text().splitlines() if x.startswith('| A01 |'))
        path.write_text(path.read_text() + line + '\n')
        self.assertIn('IDが重複', self.errors())

    def test_new_supplement_is_allowed(self):
        path = self.root / 'design/supplements.md'
        path.write_text(path.read_text() + '\n| A25 | [追加](../rules/06-adventure.md#a25) | 理由 | 影響 | 未確認 |\n')
        path = self.root / 'rules/06-adventure.md'
        path.write_text(path.read_text() + '\n<a id="a25"></a>\n\n追加の試験用補足。\n')
        self.assertEqual(self.errors(), '')

    def test_orphan_definition_is_detected(self):
        path = self.root / 'rules/06-adventure.md'
        path.write_text(path.read_text() + '\n<a id="a25"></a>\n\n台帳に未登録。\n')
        self.assertIn('台帳と本文定義', self.errors())

    def test_new_pc_is_allowed(self):
        path = self.root / 'play/sample-characters.md'
        text = path.read_text()
        pc = text.split('<a id="akira"></a>', 1)[1].split('<a id="yui"></a>', 1)[0]
        path.write_text(text + '\n<a id="another-pc"></a>' + pc.replace('アキラ', '追加PC'))
        self.assertEqual(self.errors(), '')

    def test_pc_name_is_not_fixed(self):
        self.edit('play/sample-characters.md', 'id="akira"', 'id="new-hero"')
        self.assertEqual(self.errors(), '')

    def test_bad_skill_total_is_detected(self):
        self.edit('play/sample-characters.md', '| 格闘 | 4 |', '| 格闘 | 5 |')
        self.assertIn('初期技能が不正', self.errors())

    def test_bad_hatsu_cost_is_detected(self):
        self.edit('play/sample-characters.md', '| 集束打 | 攻撃 | 3 | 0 | 0 | 0 | 0 | 0 | 3 |',
                  '| 集束打 | 攻撃 | 3 | 0 | 0 | 0 | 0 | 0 | 4 |')
        self.assertIn('構築値が不一致', self.errors())

    def test_rule_change_invalidates_stale_samples(self):
        self.edit('rules/04-nen.md', '**最大オーラ＝10＋精神×3**', '**最大オーラ＝11＋精神×3**')
        self.assertIn('最大オーラが不一致', self.errors())

    def test_formula_and_updated_samples_are_allowed(self):
        self.edit('rules/04-nen.md', '**最大オーラ＝10＋精神×3**', '**最大オーラ＝11＋精神×3**')
        self.edit('play/sample-characters.md', '最大オーラ22、現在22', '最大オーラ23、現在23')
        self.assertEqual(self.errors(), '')

    def test_pc_specific_aura_can_differ_from_shared_defaults(self):
        self.edit('play/sample-characters.md', '| 値 | 5 | 4 | 3 | 2 | 4 | 3 |',
                  '| 値 | 4 | 4 | 3 | 2 | 5 | 3 |')
        self.edit('play/sample-characters.md', '## アキラ／現場の護衛',
                  '## アキラ／現場の護衛\n\n最大オーラ25、現在25。')
        self.assertEqual(self.errors(), '')

    def test_nen_and_capacity_follow_current_rules(self):
        self.edit('rules/04-nen.md', '初期値は**3**', '初期値は**4**')
        path = self.root / 'play/sample-characters.md'
        text = path.read_text().replace('念技術3、最大オーラ', '念技術4、最大オーラ')
        text = text.replace('発容量11、負傷点', '発容量12、負傷点').replace('／11。', '／12。')
        path.write_text(text)
        self.assertEqual(self.errors(), '')

    def test_missing_rule_does_not_use_old_value(self):
        self.edit('rules/04-nen.md', '**最大オーラ＝10＋精神×3**', '最大オーラは検討中。')
        self.assertIn('最大オーラ式', self.errors())

    def test_changed_initial_skill_budget_is_read(self):
        self.edit('rules/02-checks.md', '初期技能ポイントは**25点**', '初期技能ポイントは**26点**')
        self.assertIn('初期技能が不正', self.errors())

    def test_bad_calculation_is_detected(self):
        self.edit('design/verification.md', '| `3+4+4+3` | 14 |', '| `3+4+4+3` | 15 |')
        self.assertIn('例題計算不一致', self.errors())

    def test_cli_exit_code_for_invalid_input(self):
        self.edit('README.md', 'rules/01-introduction.md', 'rules/missing.md')
        result = subprocess.run([sys.executable, str(self.root / 'scripts/validate.py')],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('リンク先なし', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_unsafe_expression_is_rejected(self):
        with self.assertRaises(ValueError):
            validate.arithmetic('__import__("os").getcwd()')


if __name__ == '__main__':
    unittest.main()
