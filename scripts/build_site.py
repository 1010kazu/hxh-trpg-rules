#!/usr/bin/env python3
"""明示したMarkdownだけを静的HTMLへ変換する。出力以外の本文は編集しない。"""
import argparse
from collections import OrderedDict
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import re
import shutil
from urllib.parse import unquote, urlsplit

import markdown

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = ('rules/', 'play/', 'scenarios/')


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain(content):
    parser = Text()
    parser.feed(content)
    return ' '.join(' '.join(parser.parts).split())


def load_pages(root):
    config = json.loads((root / 'web/site.json').read_text(encoding='utf-8'))
    seen = set()
    for page in config['pages']:
        source = page['source']
        if source in seen:
            raise ValueError('掲載元が重複しています: ' + source)
        seen.add(source)
        path = root / source
        if (source not in ('web/index.md', 'NOTICE.md') and not source.startswith(ALLOWED)) or '..' in Path(source).parts:
            raise ValueError('公開対象外のパスです: ' + source)
        if not path.is_file() or path.is_symlink() or root.resolve() not in path.resolve().parents:
            raise ValueError('掲載元が不正です: ' + source)
        page['output'] = {'web/index.md': 'index.html', 'NOTICE.md': 'notice.html'}.get(source, str(Path(source).with_suffix('.html')))
    if not {'web/index.md', 'NOTICE.md'}.issubset(seen):
        raise ValueError('入口または権利表記ページがありません')
    return config


def relative_url(current, target):
    return posixpath.relpath(target, posixpath.dirname(current) or '.')


def project_links(body, source, output, outputs):
    def rewrite(match):
        href = html.unescape(match.group(1))
        label = match.group(2)
        parts = urlsplit(href)
        if parts.scheme or parts.netloc or not parts.path:
            return match.group(0)
        target = posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(parts.path)))
        if target not in outputs:
            # 制作資料や原文へのリンクは公開HTMLへ持ち出さない。
            return '<span class="unpublished" title="この資料はサイトに掲載していません">{}</span>'.format(label)
        link = relative_url(output, outputs[target])
        if parts.fragment:
            link += '#' + parts.fragment
        return '<a href="{}">{}</a>'.format(html.escape(link, quote=True), label)
    return re.sub(r'<a href="([^"]*)">(.*?)</a>', rewrite, body, flags=re.S)


def navigation(pages, current):
    groups = OrderedDict()
    for page in pages:
        groups.setdefault(page['group'], []).append(page)
    result = []
    for group, entries in groups.items():
        result.append('<div class="nav-group"><p>{}</p><ul>'.format(html.escape(group)))
        for page in entries:
            active = ' aria-current="page"' if page['source'] == current['source'] else ''
            num = '<span class="nav-number">{}</span>'.format(page['number']) if page.get('number') else ''
            gm = '<span class="gm-mark">秘密</span>' if page.get('gm') else ''
            result.append('<li><a href="{}"{}>{}<span>{}</span>{}</a></li>'.format(
                relative_url(current['output'], page['output']), active, num, html.escape(page['title']), gm))
        result.append('</ul></div>')
    return ''.join(result)


def template(config, page, body, toc, previous, following):
    output = page['output']
    asset = relative_url(output, 'assets')
    home = relative_url(output, 'index.html')
    def pager(other, label):
        if other is None:
            return '<span></span>'
        return '<a href="{}"><small>{}</small><span>{}</span></a>'.format(
            relative_url(output, other['output']), label, html.escape(other['title']))
    warning = ('<aside class="spoiler"><strong>GM向け・ネタバレあり</strong>'
               '<p>シナリオの真相やNPCの能力を含みます。プレイヤーは導入ページをご覧ください。</p></aside>') if page.get('gm') else ''
    return '''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | HUNTER×HUNTER TRPG</title>
<meta name="description" content="念能力を自分で設計して遊ぶ、HUNTER×HUNTERの非公式TRPGルールブック。">
<link rel="stylesheet" href="{asset}/style.css"><script src="{asset}/app.js" defer></script>
</head><body data-search="{search}">
<a class="skip-link" href="#content">本文へ移動</a>
<header class="mobile-header"><a href="{home}">H×H <span>TRPG RULEBOOK</span></a><button type="button" id="menu-toggle" aria-controls="sidebar" aria-expanded="false">目次</button></header>
<aside class="sidebar" id="sidebar"><a class="brand" href="{home}"><span class="brand-icon">H<span>×</span>H</span><span>HUNTER×HUNTER<small>TRPG RULEBOOK</small></span></a>
<div class="edition"><span class="status-dot"></span>{version}</div>
<button class="search-open" type="button"><span>ルールを検索</span><kbd>/</kbd></button>
<nav aria-label="ルールブックの目次">{nav}</nav>
<div class="sidebar-footer">自分だけの念で、冒険へ。<br><span>非公式ファンメイドTRPG</span></div></aside>
<div class="page-shell"><main id="content" tabindex="-1"><div class="eyebrow">{group}<span>H×H / FIELD MANUAL</span></div>
{warning}<article>{body}</article><nav class="page-turn" aria-label="前後のページ">{prev}{next}</nav>
<footer class="page-footer">HUNTER×HUNTER TRPG <span>整理草案 / 検証・試遊中</span><button type="button" id="print-page">印刷</button></footer><div class="rights-note">本作は『HUNTER×HUNTER』の非公式二次創作TRPGです。原作者・出版社・公式関係者とは関係ありません。原作に関する権利は各権利者に帰属します。<br><a href="{notice}">二次創作・権利に関する方針</a></div></main>
<aside class="toc-panel" aria-label="このページの目次"><p>ON THIS PAGE</p>{toc}<a class="back-top" href="#content">ページの先頭へ ↑</a></aside></div>
<dialog id="search-dialog" aria-labelledby="search-title"><div class="search-heading"><h2 id="search-title">ルールを検索</h2><button type="button" id="search-close" aria-label="検索を閉じる">閉じる</button></div>
<label class="search-input-label" for="search-input">キーワード</label><input id="search-input" type="search" placeholder="オーラ、判定、発の作成…" autocomplete="off">
<label class="gm-option"><input type="checkbox" id="include-gm"> GM向けシナリオの秘密も検索する</label><p id="search-status" role="status" aria-live="polite">キーワードを入力してください。</p><ul id="search-results"></ul></dialog>
<noscript><div class="noscript-note">目次と本文はそのまま読めます。検索にはJavaScriptが必要です。</div></noscript>
</body></html>'''.format(title=html.escape(page['title']),asset=asset,search=relative_url(output,'search.json'),home=home,
                       notice=relative_url(output,'notice.html'),version=html.escape(config['version']),nav=navigation(config['pages'],page),group=html.escape(page['group']),
                       warning=warning,body=body,toc=toc,prev=pager(previous,'← 前のページ'),next=pager(following,'次のページ →'))


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        for key in ('href', 'src'):
            if key in attrs:
                self.refs.append(attrs[key])


def verify_site(output):
    """完成HTMLの全ローカルリンク・資産・フラグメントを確認する。"""
    documents = {}
    for path in output.rglob('*.html'):
        parser = Links()
        parser.feed(path.read_text(encoding='utf-8'))
        if len(parser.ids) != len(set(parser.ids)):
            raise ValueError('生成HTMLのIDが重複: ' + str(path))
        documents[path.resolve()] = parser
    for path, parser in documents.items():
        for ref in parser.refs:
            parts = urlsplit(ref)
            if parts.scheme or parts.netloc:
                continue
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            if output.resolve() not in target.parents or not target.is_file():
                raise ValueError('生成サイトのリンク切れ: {} -> {}'.format(path, ref))
            if parts.fragment and target in documents and unquote(parts.fragment) not in documents[target].ids:
                raise ValueError('生成サイトのアンカーなし: {} -> {}'.format(path, ref))
    search = json.loads((output / 'search.json').read_text(encoding='utf-8'))
    for entry in search:
        if not (output / entry['url']).is_file():
            raise ValueError('検索先がありません: ' + entry['url'])


def build(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output == root or output in root.parents or root in output.parents and output.relative_to(root).parts[0] != '_site':
        raise ValueError('出力はルートの_site配下、またはリポジトリ外を指定してください')
    # 再帰削除をせず、空の専用出力フォルダだけを使う。
    if output.exists() and any(output.iterdir()):
        raise ValueError('出力先が空ではありません。前回の生成物を別途確認してください: ' + str(output))
    config = load_pages(root)
    output.mkdir(parents=True, exist_ok=True)
    outputs = {page['source']: page['output'] for page in config['pages']}
    outputs['README.md'] = 'index.html'
    search = []
    for index, page in enumerate(config['pages']):
        source = (root / page['source']).read_text(encoding='utf-8')
        # 原文由来の「太字の次行が箇条書き」を段落と分け、読みやすく変換する。
        source = re.sub(r'(\*\*[^\n]+\*\*)\n(?=- )',r'\1\n\n',source)
        converter = markdown.Markdown(extensions=['tables','fenced_code','toc','sane_lists'],
                                      extension_configs={'toc': {'toc_depth':'2-3'}})
        body = project_links(converter.convert(source), page['source'], page['output'], outputs)
        path = output / page['output']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(template(config,page,body,converter.toc,
                                 config['pages'][index-1] if index else None,
                                 config['pages'][index+1] if index+1<len(config['pages']) else None),encoding='utf-8')
        search.append(dict(title=page['title'],url=page['output'],text=plain(body),gm=page.get('gm',False)))
    shutil.copytree(root/'web/assets',output/'assets')
    (output/'search.json').write_text(json.dumps(search,ensure_ascii=False),encoding='utf-8')
    (output/'.nojekyll').touch()
    verify_site(output)
    return len(config['pages'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'_site')
    args=parser.parse_args()
    try:
        count=build(ROOT,args.output)
    except (OSError,ValueError,KeyError) as exc:
        parser.exit(1,'ERROR: {}\n'.format(exc))
    print('PASS: {}ページを生成し、全ローカルリンクとアンカーを検証: {}'.format(count,args.output))


if __name__=='__main__':
    main()
