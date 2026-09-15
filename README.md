# dendai-skills

Codex から WebClass 取得・PDF 保存・Markdown 変換を安全に呼び出すための skill / CLI です。

## Codex Skill Usage

Codex に使わせる時は、次のように依頼します。

```text
$dendai-skills を使って。
conda/global python/curl/一時スクリプトは禁止。
/Users/med/Documents/develop/app/product/dendai-skills/.venv/bin/dendai-webclass を使い、
.env は作業ディレクトリの .env を --env で渡す。
target 側には成果物以外を書かない。
```

この skill は既存 CLI を使うためのものです。別の作業ディレクトリに `tools/fetch_*.py` のような一時スクリプトを作ったり、`curl` で WebClass ログインを再実装したりしないでください。

## Setup

```bash
python -m venv .venv
.venv/bin/python -m pip install .
```

Python 実行はこのリポジトリの `.venv` に固定します。`conda`、グローバル `python`、グローバル `pip`、グローバル `dendai-webclass` は使いません。

## Generic Usage

```bash
.venv/bin/dendai-scrape https://example.com --selector "a" --output data/example.json
```

主なオプション:

- `--selector`: CSS セレクタ。省略時は `body` を対象にします。
- `--attr`: 取得したい属性名。例: `href`
- `--limit`: 保存件数の上限。
- `--output`: 保存先 JSON パス。

HTML ファイルを直接読む場合:

```bash
.venv/bin/dendai-scrape ./sample.html --selector ".item" --output data/items.json
```

## WebClass Usage

作業ディレクトリに `.env.example` と同じ形の `.env` を置き、ログイン情報を書きます。実値入り `.env` はこのリポジトリや skill にはコピーせず、作業ディレクトリのローカルファイルとして管理してください。

```env
LOGIN_URL=https://els.sa.dendai.ac.jp/webclass/login.php
NUMBER=your-student-number
PASSWORD=your-password
```

別ディレクトリの `.env` を使う場合は `--env` で明示します。たとえば `/Users/med/Documents/university/.env` を使うなら:

detail 系の情報を JSON に保存:

```bash
/Users/med/Documents/develop/app/product/dendai-skills/.venv/bin/dendai-webclass \
  --env /Users/med/Documents/university/.env \
  --output /Users/med/Documents/university/webclass-details.json
```

資料ページ内の PDF も探して保存:

```bash
/Users/med/Documents/develop/app/product/dendai-skills/.venv/bin/dendai-webclass \
  --env /Users/med/Documents/university/.env \
  --download-pdfs \
  --pdf-dir /Users/med/Documents/university/webclass-pdfs \
  --output /Users/med/Documents/university/webclass-details.json
```

PDF を Markdown に変換して保存:

```bash
/Users/med/Documents/develop/app/product/dendai-skills/.venv/bin/dendai-webclass \
  --env /Users/med/Documents/university/.env \
  --convert-pdf-md \
  --pdf-dir /Users/med/Documents/university/webclass-pdfs \
  --markdown-dir /Users/med/Documents/university/webclass-markdown \
  --output /Users/med/Documents/university/webclass-details.json
```

## Secret Handling

- 実値入り `.env` は作業ディレクトリにだけ置きます。
- `.env` は git 管理しません。
- skill や docs に実値をコピーしません。
- 確認する場合も、値ではなくキー名だけを確認します。
