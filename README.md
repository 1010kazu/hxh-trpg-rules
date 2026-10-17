# HUNTER×HUNTER TRPG

**Ver.0.2 整理草案・初回試遊用（2026-10-17）**

原作の世界を舞台に、念能力を自分で設計して遊ぶ非公式TRPG。念を習得済みの人物となり、依頼・探索・調査・交渉・戦闘に挑む。原作既読・TRPG初心者を対象としている。実卓でのバランス検証は未実施。

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

## 制作・管理

[原文Ver.0.2](sources/ver-0.2.md)を保存し、[55節の対応表](design/source-map.md)で移植先を追跡している。原文の数値は維持し、不足処理は本文の「暫定補足 Axx」に明示した。原文の暫定値・要テスト項目は引き続き暫定扱い。

[制作規約](AGENTS.md)／[制作スキル](skills/hxh-rulebook/SKILL.md)／[暫定補足台帳](design/supplements.md)／[調整課題](design/open-questions.md)／[変更履歴](design/changelog.md)／[検証記録](design/verification.md)／[更新・検証・保存の手順](design/workflow.md)

検証コマンド：`python3 scripts/validate.py`（Python 3標準ライブラリのみ）。保存先は [1010kazu/hxh-trpg-rules](https://github.com/1010kazu/hxh-trpg-rules)、非公開、既定ブランチ `main`。今後の更新は検証後にコミット・pushし、同期を確認する。
