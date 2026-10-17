#!/usr/bin/env python3
"""原文保存・参照・現行ルールに基づくサンプルを検証。ゲーム進行は扱わない。"""
import ast
import hashlib
import operator
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = '30463ca2634319dd9e61b24018e6ee9e7992e2e13aa826ea92e56925e0072a55'


def read(path):
    return path.read_text(encoding='utf-8')


def prose(text):
    return re.sub(r'```.*?```|~~~.*?~~~', '', text, flags=re.S)


def table_rows(text):
    return [[cell.strip() for cell in line.strip().strip('|').split('|')]
            for line in text.splitlines() if line.startswith('|')]


def arithmetic(expression, names=None):
    """数字・指定した名前・四則演算だけを評価。evalや任意コード実行は使わない。"""
    ops = {ast.Add: operator.add, ast.Sub: operator.sub,
           ast.Mult: operator.mul, ast.Div: operator.truediv}
    names = {} if names is None else names

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.Name) and node.id in names:
            return names[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            return ops[type(node.op)](visit(node.left), visit(node.right))
        raise ValueError('許可されていない数式: ' + expression)
    return visit(ast.parse(expression, mode='eval'))


def one(pattern, text, label):
    values = re.findall(pattern, text, flags=re.M)
    if len(values) != 1:
        raise ValueError('{}: 定義を一意に読み取れません（{}件）'.format(label, len(values)))
    return values[0]


def section(text, anchor):
    """明示アンカーから次の同形式アンカーまで。本文の完全一致は要求しない。"""
    start = '<a id="{}"></a>'.format(anchor)
    if text.count(start) != 1:
        raise ValueError('アンカーが一意ではありません: ' + anchor)
    return re.split(r'<a id="[^"]+"></a>', text.split(start, 1)[1], maxsplit=1)[0]


def markdown_files(root):
    files = []
    for directory, subdirs, names in os.walk(root, followlinks=False):
        subdirs[:] = [name for name in subdirs if not name.startswith('.')
                      and not (Path(directory) / name).is_symlink()]
        files.extend(Path(directory) / name for name in names
                     if name.endswith('.md') and not name.startswith('.')
                     and not (Path(directory) / name).is_symlink())
    return sorted(files)


def rule_values(mapped):
    """原文対応表が指す現行本文の定義を読む。読めなければ失敗させる。"""
    ability = mapped[4].replace('**', '')
    skill = mapped[5].replace('**', '')
    nen = mapped[9].replace('**', '')
    names = re.findall(r'^- (\S+)$', re.split(r'値は\d+～', ability, maxsplit=1)[0], re.M)
    count = int(one(r'能力値は(\d+)種類', ability, '能力値の数'))
    if len(names) != count or len(set(names)) != count:
        raise ValueError('能力値の一覧と種類数が一致しません')
    low, high = one(r'^値は(\d+)～(\d+)。$', ability, '能力値範囲')
    skills = one(r'^#{2,6} 暫定技能\n\n([^\n]+)。$', skill, '技能一覧').split('、')
    if len(set(skills)) != len(skills):
        raise ValueError('技能一覧が重複しています')
    aura = one(r'^最大オーラ＝([^\n]+)$', mapped[8].replace('**', ''), '最大オーラ式')
    capacity = one(r'^発容量＝([^\n]+)$', mapped[12].replace('**', ''), '発容量式')
    translate = str.maketrans({'＋': '+', '－': '-', '×': '*', '÷': '/'})
    return dict(abilities=names, low=int(low), high=int(high), skills=set(skills),
                ability_total=int(one(r'能力値合計は(\d+)', ability, '能力値合計')),
                skill_total=int(one(r'初期技能ポイントは(\d+)点', skill, '初期技能ポイント')),
                skill_max=int(one(r'初期技能値上限は(\d+)', skill, '初期技能上限')),
                nen=int(one(r'初期値は(\d+)', nen, '初期念技術')),
                aura=aura.translate(translate), capacity=capacity.translate(translate))


class Validator:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.errors = []
        self.counts = dict(sections=0, links=0, supplements=0, pcs=0, hatsu=0, calculations=0)

    def check(self, condition, message):
        if not condition:
            self.errors.append(message)

    def path(self, filename):
        return self.root / filename

    def local_target(self, parent, target):
        filename, _, fragment = unquote(target).partition('#')
        path = (parent / filename).resolve()
        if path != self.root and self.root not in path.parents:
            raise ValueError('リポジトリ外への参照: ' + target)
        if not path.is_file():
            raise ValueError('リンク先なし: ' + target)
        return path, fragment

    def sources(self):
        source = self.path('sources/ver-0.2.md')
        self.check(hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA,
                   '保存原文のSHA-256が変わっています')
        source_ids = re.findall(r'^#{1,2} (\d+)\. ', read(source), re.M)
        self.check(len(source_ids) == 55 and set(map(int, source_ids)) == set(range(1, 56)),
                   '保存原文が55節揃っていません')
        entries = re.findall(r'^\| (\d+) \| .*? \| \[本文\]\(([^)]+)\) \|$',
                             read(self.path('design/source-map.md')), re.M)
        self.check(len(entries) == len(source_ids) and {n for n, _ in entries} == set(source_ids),
                   '原文対応表の節番号に不足または重複があります')
        mapped = {}
        for number, target in entries:
            path, anchor = self.local_target(self.path('design'), target)
            if not anchor:
                raise ValueError('原文対応先には節アンカーが必要: ' + target)
            body = section(read(path), anchor)
            # 見出し・出典・ナビゲーションだけを残した空節を検出する。
            substantive = re.sub(r'^#+ .*?$|^出典：.*?$|^\[目次に戻る\].*?$', '', body, flags=re.M)
            self.check(bool(substantive.strip()), '原文対応先の本文が空です: ' + target)
            mapped[int(number)] = body
        self.counts['sections'] = len(mapped)
        return mapped

    def links(self):
        for path in markdown_files(self.root):
            content = prose(read(path))
            label = str(path.relative_to(self.root))
            if label != 'sources/ver-0.2.md':
                self.check(len(re.findall(r'^# ', content, re.M)) == 1, label + ': 最上位見出しは1つ必要')
            anchors = re.findall(r'<a id="([^"]+)"></a>', content)
            self.check(len(anchors) == len(set(anchors)), label + ': アンカー重複')
            for target in re.findall(r'\[[^\]\n]+\]\(([^)\n]+)\)', content):
                if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                    continue
                self.counts['links'] += 1
                try:
                    dest, anchor = self.local_target(path.parent, path.name + target if target.startswith('#') else target)
                    if anchor:
                        self.check('<a id="{}"></a>'.format(anchor) in prose(read(dest)),
                                   label + ': 明示アンカーなし ' + target)
                except ValueError as exc:
                    self.check(False, label + ': ' + str(exc))

    def supplements(self):
        ledger = read(self.path('design/supplements.md'))
        ids = re.findall(r'^\| (A\d+) \|', ledger, re.M)
        rule_text = '\n'.join(prose(read(p)) for p in sorted(self.path('rules').glob('*.md')))
        definitions = re.findall(r'<a id="(a\d+)"></a>', rule_text)
        self.check(len(ids) == len(set(ids)), '暫定補足台帳のIDが重複しています')
        self.check(len(definitions) == len(set(definitions)), '暫定補足の本文定義が重複しています')
        self.check({x.lower() for x in ids} == set(definitions), '暫定補足台帳と本文定義に不足があります')
        self.counts['supplements'] = len(ids)

    def samples(self, rules):
        sample = read(self.path('play/sample-characters.md'))
        blocks = re.split(r'<a id="([^"\n]+)"></a>\s*\n\s*## ', sample)
        self.check(len(blocks) > 1, 'サンプルPCがありません')
        defaults = blocks[0]
        # 現行のMarkdown形式。個別PCに同名の項目を書けば共通値を上書きできる。
        def value(block, key):
            pattern = re.escape(key) + r'[：:]?(\d+)'
            found = re.findall(pattern, block)
            if found:
                if len(set(found)) != 1:
                    raise ValueError('サンプルの' + key + 'の記載が矛盾しています')
                return int(found[0])
            return int(one(pattern, defaults, 'サンプル共通' + key))

        for index in range(1, len(blocks), 2):
            pc, block = blocks[index:index + 2]
            self.counts['pcs'] += 1
            # 説明文や発本文に現れる数値は初期値の宣言として読まない。
            metadata = block.split('| 能力値 |', 1)[0]
            rows = table_rows(block)
            ability_rows = [r for r in rows if r[0] == '値']
            ability_headers = [r for r in rows if r[0] == '能力値']
            if len(ability_rows) != 1 or len(ability_headers) != 1:
                raise ValueError(pc + ': 能力値表を一意に読めません')
            values = list(map(int, ability_rows[0][1:]))
            self.check(ability_headers[0][1:] == rules['abilities'], pc + ': 能力値の種類が不一致')
            self.check(len(values) == len(rules['abilities']) and sum(values) == rules['ability_total']
                       and all(rules['low'] <= n <= rules['high'] for n in values), pc + ': 能力値が不正')
            if len(values) != len(rules['abilities']):
                continue
            nen = value(metadata, '念技術')
            expansion = value(metadata, '容量拡張')
            self.check(nen == rules['nen'] and expansion == 0, pc + ': 初期念技術・容量拡張が不正')
            names = dict(zip(rules['abilities'], values), 念技術=nen, 容量拡張=expansion)
            aura = arithmetic(rules['aura'], names)
            capacity = arithmetic(rules['capacity'], names)
            self.check(value(metadata, '最大オーラ') == aura, pc + ': 最大オーラが不一致')
            self.check(value(metadata, '現在') == aura and value(metadata, '拘束') == 0,
                       pc + ': 初期現在・拘束オーラが不一致')
            self.check(value(metadata, '発容量') == capacity, pc + ': 発容量が不一致')
            skills = [(r[0], int(r[1])) for r in rows if len(r) == 2 and re.fullmatch(r'-?\d+', r[1])]
            self.check(sum(v for _, v in skills) == rules['skill_total']
                       and all(0 <= v <= rules['skill_max'] for _, v in skills), pc + ': 初期技能が不正')
            self.check(len({s for s, _ in skills}) == len(skills)
                       and all(s in rules['skills'] for s, _ in skills), pc + ': 技能名の重複または誤記')
            hatsu = [r for r in rows if len(r) == 9 and re.fullmatch(r'-?\d+', r[2])]
            self.check(bool(hatsu), pc + ': 発の構築表がありません')
            for row in hatsu:
                costs = list(map(int, row[2:8]))
                self.check(all(n >= 0 for n in costs) and sum(costs) == int(row[8]),
                           pc + ' ' + row[0] + ': 構築値が不一致')
            total = sum(int(r[8]) for r in hatsu)
            self.counts['hatsu'] += len(hatsu)
            displayed = one(r'全発構築値合計：(\d+)／(\d+)', block, pc + 'の構築値合計')
            self.check(total <= capacity and tuple(map(int, displayed)) == (total, capacity),
                       pc + ': 構築値合計・容量が不一致')

    def calculations(self):
        for row in table_rows(read(self.path('design/verification.md'))):
            if len(row) == 3 and row[1].startswith('`'):
                self.check(bool(re.fullmatch(r'-?\d+(?:\.\d+)?', row[2])), '例題の期待値が不正: ' + row[0])
                if not re.fullmatch(r'-?\d+(?:\.\d+)?', row[2]):
                    continue
                self.check(arithmetic(row[1].strip('`')) == float(row[2]), '例題計算不一致: ' + row[0])
                self.counts['calculations'] += 1
        self.check(self.counts['calculations'] > 0, '計算例がありません')

    def run(self):
        for label, action in [('原文・対応表', self.sources), ('相対参照', self.links),
                              ('暫定補足', self.supplements), ('計算例', self.calculations)]:
            try:
                result = action()
                if label == '原文・対応表':
                    self.mapped = result
            except (OSError, ValueError, KeyError, SyntaxError, ZeroDivisionError) as exc:
                self.check(False, label + ': ' + str(exc))
        try:
            self.samples(rule_values(self.mapped))
        except (OSError, ValueError, KeyError, AttributeError, SyntaxError, ZeroDivisionError) as exc:
            self.check(False, '現行定義・サンプル: ' + str(exc))
        return self.errors


def main():
    validator = Validator(ROOT)
    errors = validator.run()
    if errors:
        for error in errors:
            print('ERROR:', error, file=sys.stderr)
        return 1
    c = validator.counts
    print('PASS: 原文SHA-256、対応先{sections}節、相対参照{links}件、補足{supplements}件、PC{pcs}人・発{hatsu}件、計算例{calculations}件'.format(**c))
    print('本文の原文一致・AI模擬試遊・実卓バランス・外部保存は自動判定しません。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
