# HUNTER×HUNTER TRPG

**Ver.0.3 統合版・実卓未検証（2026-11-23）**

[Ver.0.3の通読用本文](rules/ver-0.3.md)。章別本文とプレイ資料も同じ版を参照する。

原作の世界を舞台に、念能力を自分で設計して遊ぶ非公式TRPG。念を習得済みの人物となり、依頼・探索・調査・交渉・戦闘に挑む。原作既読・TRPG初心者を対象としている。実卓でのバランス検証は未実施。

## ブラウザで読む

**[公開ルールブックを読む](https://1010kazu.github.io/hxh-trpg-rules/)**

章メニュー・ページ内目次・検索・スマートフォン表示・印刷に対応した閲覧サイトを用意しています。ルール本文・プレイ資料・GM用シナリオ・権利表記の19ページを掲載対象とし、制作資料・AI試遊記録・保存原文は掲載しません。GitHub Pagesで公開し、mainへの更新時に検証・再公開します。

ローカルで読むには、リポジトリのルートで次を実行してください。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r web/requirements.txt
.venv/bin/python scripts/build_site.py
.venv/bin/python -m http.server 8000 --bind 127.0.0.1 --directory _site
```

ブラウザで `http://127.0.0.1:8000/` を開きます。終了はターミナルでCtrl+C。再ビルド時は生成物のみの `_site` フォルダを削除するか、`--output` で別の空フォルダを指定してください。HTMLを直接開く場合は検索データを取得できないことがあるため、上のローカルサーバーを使用します。

サイトの構成は [web/site.json](web/site.json)、生成は [scripts/build_site.py](scripts/build_site.py)、更新・公開の運用は[運用ガイド](design/workflow.md)を参照してください。

## はじめて遊ぶ

1. [はじめに](rules/01-introduction.md)でGM・プレイヤーの役割を知る。
2. [基本判定](rules/02-checks.md)を読み、[サンプルPC3人](play/sample-characters.md)から選ぶか[キャラクター作成](rules/03-character-creation.md)を行う。
3. [念](rules/04-nen.md)、[発の作成](rules/05-hatsu.md)、[戦闘](rules/07-combat.md)を読む。
4. [導入シナリオ・プレイヤー向け](scenarios/01-missing-cargo-player.md)を読む。GMだけは[GM用シナリオ・秘密あり](scenarios/01-missing-cargo-gm.md)も読む。
5. 遊びながら[早見表](play/quick-reference.md)を参照し、終了時に[成長](rules/09-advancement.md)を行う。

## ルールブック目次

| 章 | 内容 |
|---|---|
| [1 はじめに](rules/01-introduction.md) | 準備、役割、進め方、設計思想 |
| [2 基本判定](rules/02-checks.md) | 判定、技能、専門、特殊出目 |
| [3 キャラクター作成](rules/03-character-creation.md) | 作成順序、能力値、チェック |
| [4 念](rules/04-nen.md) | オーラ、系統、基礎念技術 |
| [5 発の作成](rules/05-hatsu.md) | 強度、構築、消費、制約、治療発 |
| [6 探索・調査・交渉](rules/06-adventure.md) | 情報、協力、再挑戦 |
| [7 戦闘](rules/07-combat.md) | 行動、配分、攻撃、拘束・操作 |
| [8 装備・負傷・回復](rules/08-equipment-and-recovery.md) | 装備、負傷、医学、休息 |
| [9 成長](rules/09-advancement.md) | 成長点、チェック、発の成長 |
| [10 GMガイド](rules/10-gm-guide.md) | 裁定、情報提示、NPC作成 |

## プレイ用資料

- [キャラクターシート](play/character-sheet.md)／[発の設計シート](play/hatsu-sheet.md)
- [サンプルPCと発](play/sample-characters.md)
- [早見表](play/quick-reference.md)／[用語集](play/glossary.md)

## 二次創作・権利について

本作は、冨樫義博先生の『HUNTER×HUNTER』（集英社）を題材とする非公式の二次創作TRPGです。原作者・出版社などの公式関係者とは関係がなく、原作に関する権利は各権利者に帰属します。原作と公式活動を尊重し、本作に関する公式窓口へのお問い合わせはお控えください。詳しくは[二次創作・権利に関する方針](NOTICE.md)をご覧ください。

## 制作・管理

**[検討課題のIssue一覧](https://github.com/1010kazu/hxh-trpg-rules/issues)**で暫定補足・バランス調整・裁定整理を検討する。`種類:`・`分野:`・`状況:` のラベルで絞り込める。A番号は[暫定補足台帳](design/supplements.md)、Q番号とAI試遊のT番号は[調整課題](design/open-questions.md)から参照できる。議論と進捗はIssue、現行のルール定義は本文に残す。採用時はユーザーとの合意と必要な反映・検証・AI試遊を終え、見送り時は理由を残してクローズする。

[原文Ver.0.2](sources/ver-0.2.md)を保存し、[55節の対応表](design/source-map.md)で移植先を追跡している。原文の数値は維持し、不足処理は本文の「暫定補足 Axx」に明示した。原文の暫定値・要テスト項目は引き続き暫定扱い。

[制作規約](AGENTS.md)／[制作スキル](skills/hxh-rulebook/SKILL.md)／[暫定補足台帳](design/supplements.md)／[調整課題](design/open-questions.md)／[変更履歴](design/changelog.md)／[検証記録](design/verification.md)／[AI試遊記録・GM用の秘密あり](design/playtests/2026-10-18-ver-0.2-baseline.md)／[更新・検証・保存の手順](design/workflow.md)

検証コマンド：`python3 scripts/validate.py`、回帰テスト：`python3 -m unittest discover -s tests -v`（Python 3.8以上・標準ライブラリのみ）。GitHub Actionsでも検証する。ルール改訂時はAIが境界ケースと導入シナリオを試遊し、結果を記録する。保存先は [1010kazu/hxh-trpg-rules](https://github.com/1010kazu/hxh-trpg-rules)、公開リポジトリ、既定ブランチ `main`。今後の更新は検証後にコミット・pushし、同期を確認する。

バージョンごとの管理Issue・マイルストーン、検討から統合・試遊・次版への引き継ぎは[バージョン運用](design/workflow.md#version-cycle)に従う。
