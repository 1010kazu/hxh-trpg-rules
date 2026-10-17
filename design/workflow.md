# ルールブックの更新・検証・保存

保存先：[1010kazu/hxh-trpg-rules](https://github.com/1010kazu/hxh-trpg-rules)。非公開、既定ブランチ `main`、リモート名 `origin`。すでに連携済みのため、Git初期化・リポジトリ作成は不要。

## 更新を始める

リポジトリのルートで実行する。

```bash
git status --short --branch
git remote -v
git fetch origin
git log --oneline --left-right HEAD...origin/main
```

作業中の変更と今回の変更を区別する。作業ツリーがきれいで、ローカルがリモートより遅れているだけなら `git pull --ff-only origin main` で取り込む。ローカルにも独自コミットがある場合は履歴を比較して統合する。未コミットの変更を勝手に破棄・退避せず、競合時も既存作業を保つ。強制pushで解消しない。

## 内容を更新する

[制作規約](../AGENTS.md)と[制作スキル](../skills/hxh-rulebook/SKILL.md)に従い、目的に応じて次を更新する。

| 更新する内容 | 合わせて確認する資料 |
|---|---|
| ルール本文 | 関連するシート、サンプル、早見表、シナリオ |
| 未定義の処理の補足 | [暫定補足台帳](supplements.md)と本文の定義箇所 |
| 数値・設計の変更案 | [調整課題](open-questions.md)に理由と影響を記録し、合意後に本文へ採用 |
| 章の移動・参照先の変更 | [原文対応表](source-map.md)と相対リンク |
| 検証・試遊の結果 | [検証記録](verification.md)、実卓で判明した課題 |
| 読者や制作者に影響する変更 | [変更履歴](changelog.md) |

保存原文 `sources/ver-0.2.md` は編集しない。`.gitattributes` は原文の改行を含むバイト保持とMarkdownの改行記法に合わせている。ファイルの追加・削除・改名時は、入口と参照元も更新する。

## 検証してコミットする

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
git diff --check
git diff --stat
git diff
```

検証対象には原文ハッシュと55節の対応先、相対リンク、補足台帳、現行本文の定義に基づくサンプル数値、計算例が含まれる。原文と改訂後の本文の文章一致は要求しない。本文の初期値や計算式を読み取れない場合は失敗するため、定義の書式を変更したときは読み取り処理と回帰テストも更新する。関連するプレイ手順も読み直し、何を確認し、何が未確認かを検証記録に残す。実卓テスト・AI模擬試遊・机上確認を区別する。制作スキルを変更した場合は、利用可能なら skill-creator の `quick_validate.py` でも検証する。

今回変更したファイルを指定して登録する。以下は判定ルールを変更した場合の例であり、実際の対象に合わせて置き換える。新規ファイル・削除したファイルも対象に含める。

```bash
git add -- rules/02-checks.md design/changelog.md design/verification.md
git diff --cached --check
git diff --cached --stat
git diff --cached
git commit -m "docs: clarify opposed check rules"
```

他の作業者の変更や認証ファイルを混ぜない。コミットメッセージは変更の目的が分かる内容にする。変更がない場合は空のコミットを作らない。

## AIによる模擬試遊

ルールの処理・数値・発や装備の性能を変更する場合は、コミット前に変更箇所の境界ケース確認と、導入シナリオ1回の通し試遊を実施する。誤字修正・運用資料のみの変更は対象外。ゲーム進行スクリプトやGitHub Actionsで代行せず、この制作作業を担当するAIが実行する。

1. [試遊テンプレート](playtests/template.md)を `design/playtests/YYYY-MM-DD-内容.md` に複製し、対象コミット・未コミット差分・使用シナリオとPC・変更点を記す。同日複数回は末尾に連番を付ける。
2. 初期状態を定め、GMだけの秘密とPCが獲得済みの情報を分けて進行する。行動・対象・対応・補正を決めた後に乱数ツールで振り、出目を採用する。計算補助は可、ゲームの判断・進行・評価はAIが行う。
3. 主要な判定と、オーラ・拘束・配分・負傷・行動回数の変化を記録し、結末・回復・成長まで進める。戦闘がなければ別場面で補い、その状態を通し試遊へ混ぜない。
4. 未定義の処理は記録する。仮裁定で進めるなら先に条件を明示する。続行不能なら停止地点を残す。境界条件を狙った指定出目の確認は、通常の乱数試遊と区別する。
5. 「確認範囲で問題なし／要調整／進行不能」で結論を残し、発見を[調整課題](open-questions.md)へ登録する。数値・既存設計の変更は相談後に採用。最終稿でルールが再変更されたら試遊も再確認する。

[初回記録・GM用の秘密あり](playtests/2026-10-18-ver-0.2-baseline.md)を形式の例にできる。人間の実卓テストは別に記録し、AIの確認だけで楽しさ・全体バランス・人間の所要時間を保証しない。

## GitHubへ保存し、同期を確認する

```bash
git push origin main
git status --short --branch
git rev-parse HEAD
git ls-remote origin refs/heads/main
gh repo view 1010kazu/hxh-trpg-rules --json nameWithOwner,isPrivate,defaultBranchRef
```

ローカルHEADとリモートmainのハッシュ一致、保存先名、`isPrivate: true`、既定ブランチ `main` を確認する。今回の変更が残っていないことも確認する。他の作業者の未コミット変更がある場合は、それを残したまま区別して報告する。

このリポジトリで依頼された更新は、ユーザーから別の指定がなければ、検証・コミット・push・同期確認まで行う。報告には変更内容、検証結果、コミット、保存状況を含める。pushに失敗した場合はローカルのコミットを残し、未保存であることと原因を伝える。

## GitHub Actionsの結果を確認する

[検証ワークフロー](../.github/workflows/validate.yml)はpush、main宛てのPR、手動実行で起動し、Python 3.12で検証スクリプトと回帰テストを実行する。追加の秘密鍵やAI APIは使わない。ローカルはPython 3.8以上・標準ライブラリで実行可能。Actionsには読み取り権限だけを与える。

```bash
gh run list --workflow validate.yml --commit "$(git rev-parse HEAD)"
gh run view RUN_ID --exit-status
```

`RUN_ID` は対象コミットの実行IDに置き換える。待機中なら `gh run watch RUN_ID --exit-status` で結果を確認する。失敗したらログを調べ、関連箇所を修正・再検証して保存する。実行自体が無効化されている場合は、ローカル検証結果とCI未確認を分けて報告する。AI模擬試遊の実施・妥当性はCIの合格では証明できず、記録をAIが確認する。

## 認証・権限・競合で止まった場合

まずエラーを読み、認証不備、ネットワーク制限、Git管理領域の書き込み制限、リモートとの競合を区別する。実行環境の制限であれば、必要なコマンドを承認付きで再実行する。サンドボックス内の接続失敗だけで認証切れと判断しない。

通常の端末でも認証に失敗する場合に限り、以下で確認・再ログインする。

```bash
gh auth status
gh auth login --hostname github.com --git-protocol https --web
gh auth switch --hostname github.com --user 1010kazu
gh api user --jq .login
```

pushがリモートの更新で拒否された場合はfetchして差分を確認し、既存の変更と統合して再検証する。既存リポジトリの再作成や履歴の強制上書きは行わない。
