#!/usr/bin/env python3
"""保存原文・移植網羅・Markdown参照・サンプル計算を検証する（標準ライブラリのみ）。"""
import ast
import hashlib
import operator
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
ERRORS = []


def check(condition, message):
    if not condition:
        ERRORS.append(message)


def read(path):
    return path.read_text(encoding='utf-8')


def sections(text):
    parts = re.split(r'(?m)^#{1,2} (\d+)\. (.+)\n', text)
    return {int(parts[i]): (parts[i + 1], re.sub(r'\n---\s*$', '', parts[i + 2].strip()))
            for i in range(1, len(parts), 3)}


def table_rows(text):
    return [[cell.strip() for cell in line.strip().strip('|').split('|')]
            for line in text.splitlines() if line.startswith('|')]


def arithmetic(expression):
    """検証記録に記載した四則演算のみ評価する。任意コードは実行しない。"""
    ops = {ast.Add: operator.add, ast.Sub: operator.sub,
           ast.Mult: operator.mul, ast.Div: operator.truediv}

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            return ops[type(node.op)](visit(node.left), visit(node.right))
        raise ValueError('許可されていない数式: ' + expression)
    return visit(ast.parse(expression, mode='eval'))


def main():
    original = ROOT / 'sources/ver-0.2.md'
    digest = hashlib.sha256(original.read_bytes()).hexdigest()
    # 添付ファイルを保存した時点のSHA-256。原文は編集対象にしない。
    check(digest == '30463ca2634319dd9e61b24018e6ee9e7992e2e13aa826ea92e56925e0072a55', '保存原文のSHA-256が変わっています')
    source_sections = sections(read(original))
    check(set(source_sections) == set(range(1, 56)), '原文が55節揃っていません')
    mapping = read(ROOT / 'design/source-map.md')
    entries = re.findall(r'^\| (\d+) \| .*? \| \[本文\]\(([^)]+)\) \|$', mapping, re.M)
    check(len(entries) == 55 and {int(n) for n, _ in entries} == set(range(1, 56)),
          '原文対応表の節番号に不足または重複があります')
    for number, target in entries:
        n = int(number)
        target_file = (ROOT / 'design' / target.split('#')[0]).resolve()
        if not target_file.exists():
            check(False, '移植先なし: ' + target)
            continue
        body = source_sections[n][1]
        if n != 54:
            body = re.sub(r'(?m)^(#{1,5}) ', r'#\1 ', body)
        check(body in read(target_file), '原文第{}節の内容が移植先と一致しません'.format(n))

    markdown = sorted(ROOT.rglob('*.md'))
    links = 0
    for path in markdown:
        content = read(path)
        if path != original:
            check(len(re.findall(r'^# ', content, re.M)) == 1,
                  '{}: 最上位見出しは1つにしてください'.format(path.relative_to(ROOT)))
        anchors = re.findall(r'<a id="([^"]+)"></a>', content)
        check(len(anchors) == len(set(anchors)), '{}: アンカー重複'.format(path))
        # コードブロック内のコマンドは参照の対象外。
        prose = re.sub(r'```.*?```', '', content, flags=re.S)
        for target in re.findall(r'\[[^\]\n]+\]\(([^)\n]+)\)', prose):
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                continue
            links += 1
            file_part, sep, fragment = unquote(target).partition('#')
            dest = (path.parent / file_part).resolve() if file_part else path
            check(ROOT == dest or ROOT in dest.parents, '{}: リポジトリ外への参照 {}'.format(path, target))
            check(dest.is_file(), '{}: リンク先なし {}'.format(path.relative_to(ROOT), target))
            if sep and dest.is_file():
                check('<a id="{}"></a>'.format(fragment) in read(dest),
                      '{}: 明示アンカーなし {}'.format(path.relative_to(ROOT), target))

    ledger = read(ROOT / 'design/supplements.md')
    ids = re.findall(r'^\| (A\d+) \|', ledger, re.M)
    check(len(ids) == 24 and set(ids) == {'A{:02d}'.format(n) for n in range(1, 25)},
          '暫定補足台帳に不足または重複があります')
    rule_text = '\n'.join(read(p) for p in sorted((ROOT / 'rules').glob('*.md')))
    for item in ids:
        check(rule_text.count('<a id="{}"></a>'.format(item.lower())) == 1,
              item + ': 本文の定義位置が一意ではありません')

    sample = read(ROOT / 'play/sample-characters.md')
    blocks = re.split(r'<a id="(akira|yui|mio)"></a>', sample)
    check(len(blocks) == 7, 'サンプルPC3人の区切りがありません')
    skill_names = set(re.findall(r'^\| ([^|]+?) \|', read(ROOT / 'play/character-sheet.md'), re.M))
    for index in range(1, len(blocks), 2):
        name, block = blocks[index:index + 2]
        rows = table_rows(block)
        abilities = [int(c) for r in rows if r[0] == '値' for c in r[1:]]
        check(len(abilities) == 6 and sum(abilities) == 21 and all(1 <= n <= 6 for n in abilities),
              name + ': 能力値が不正です')
        if len(abilities) == 6:
            check(10 + abilities[4] * 3 == 22, name + ': 最大オーラ22と不一致です')
        skills = [(r[0], int(r[1])) for r in rows if len(r) == 2 and r[1].isdigit()]
        check(sum(v for _, v in skills) == 25 and all(0 <= v <= 4 for _, v in skills),
              name + ': 初期技能が不正です')
        check(len({s for s, _ in skills}) == len(skills) and all(s in skill_names for s, _ in skills),
              name + ': 技能名の重複または誤記です')
        hatsu = [r for r in rows if len(r) == 9 and r[2].isdigit()]
        check(bool(hatsu), name + ': 発がありません')
        for row in hatsu:
            costs = [int(v) for v in row[2:8]]
            check(sum(costs) == int(row[8]), name + ' ' + row[0] + ': 構築値が不一致です')
        total = sum(int(r[8]) for r in hatsu)
        check(total <= 8 + 3, name + ': 容量超過です')
        check('全発構築値合計：{}／11'.format(total) in block, name + ': 構築値合計の表示が不一致です')

    calculations = 0
    for row in table_rows(read(ROOT / 'design/verification.md')):
        if len(row) == 3 and row[1].startswith('`') and row[2].isdigit():
            expression = row[1].strip('`')
            try:
                check(arithmetic(expression) == int(row[2]), '例題計算不一致: ' + row[0])
                calculations += 1
            except (ValueError, SyntaxError) as exc:
                check(False, str(exc))
    check(calculations >= 15, '計算例の検証が不足しています')
    if ERRORS:
        for error in ERRORS:
            print('ERROR:', error, file=sys.stderr)
        return 1
    print('PASS: 原文SHA-256、55節の本文保持、{}件の相対参照、暫定補足24件、PC3人・発4つ、例題{}件'.format(links, calculations))
    print('対象Markdown: {}ファイル。実卓バランス・外部保存は検証対象外。'.format(len(markdown)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
