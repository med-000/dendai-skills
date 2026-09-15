# dendai-skills

BeautifulSoup でページを取得し、抽出結果を JSON に保存するためのスクレイピング土台です。

## Setup

```bash
python -m venv .venv
.venv/bin/python -m pip install .
```

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

別ディレクトリの `.env` を使う場合は `--env` で明示します。

detail 系の情報を JSON に保存:

```bash
.venv/bin/dendai-webclass --env /path/to/workdir/.env --output data/webclass-details.json
```

資料ページ内の PDF も探して保存:

```bash
.venv/bin/dendai-webclass --env /path/to/workdir/.env --download-pdfs --pdf-dir data/pdfs --output data/webclass-details.json
```

PDF を Markdown に変換して保存:

```bash
.venv/bin/dendai-webclass --env /path/to/workdir/.env --convert-pdf-md --pdf-dir data/pdfs --markdown-dir data/markdown --output data/webclass-details.json
```
