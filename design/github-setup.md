# Git・GitHubへの保存

保存予定：`1010kazu/hxh-trpg-rules`、非公開、既定ブランチ `main`。

## 現在の状態

この実行環境は `.git` を書き込み禁止としており、まだGitリポジトリとして初期化できていない。GitHub CLIには1010kazuが登録されているが認証が失敗するため、外部リポジトリの有無・公開設定・push完了は確認できていない。以下はユーザーの通常の端末で実行する。作成・pushが終わるまではGitHubに保存済みとは扱わない。

## 認証と保存先の確認

```bash
cd /home/butamen/hxh-trpg-rules
python3 scripts/validate.py
gh auth login --hostname github.com --git-protocol https --web
gh auth switch --hostname github.com --user 1010kazu
gh api user --jq .login
gh repo view 1010kazu/hxh-trpg-rules --json nameWithOwner,isPrivate,url,defaultBranchRef
```

ログイン名が1010kazuであることを確認する。最後のコマンドが失敗したら、まず権限・ネットワーク等のエラーと「存在しない」を区別する。

既存リポジトリがあれば、その非公開設定と内容・履歴を確認して接続する。公開リポジトリへこの内容をpushしない。既存履歴を上書きせず、既存ファイルがある場合はクローン先で比較・統合する。以下の新規作成コマンドは使わない。

## 同名リポジトリが存在しない場合

元の作業フォルダで実行する。Git管理領域のロックはこの作業環境の制約であり、端末側でも権限エラーになる場合はそこで止め、権限のある場所へ本文をコピーして初期化する。`.git` の削除や権限変更で回避しない。

```bash
git init
git symbolic-ref HEAD refs/heads/main
git config user.name 1010kazu
git config user.email 1010kazu@users.noreply.github.com
git add -- .gitignore AGENTS.md README.md sources rules play scenarios design skills scripts
git diff --cached --stat
git diff --cached --check
git commit -m "docs: add HUNTER x HUNTER TRPG playtest rulebook"
gh auth setup-git --hostname github.com
gh repo create 1010kazu/hxh-trpg-rules --private --source=. --remote=origin --push
```

Gitの署名設定や作者情報は端末の方針に合わせて調整できる。上記の作者設定はこのリポジトリに限って適用する。

## 保存後の確認

```bash
git status --short --branch
git remote -v
git rev-parse HEAD
git ls-remote origin refs/heads/main
gh repo view 1010kazu/hxh-trpg-rules --json nameWithOwner,isPrivate,url,defaultBranchRef
```

名前が指定どおり、`isPrivate` がtrue、既定ブランチがmain、ローカルHEADとリモートmainのハッシュが同じことを確認する。pushが部分的に失敗した場合は同名リポジトリを再作成せず、状態を読み直す。既定ブランチだけが異なる新規リポジトリなら `gh repo edit 1010kazu/hxh-trpg-rules --default-branch main` で設定して再確認する。

完了後は[入口](../README.md)と[変更履歴](changelog.md)の保存状態を更新し、その修正もcommit・pushする。
