# Dendai WebClass Scraper

Use this reference for the `dendai-skills` WebClass scraper.

## Scope Discipline

This reference describes how to work inside the existing `dendai-skills` scraper. Do not use it as a reason to decompose skills, move packages, rename commands, or rewrite unrelated application structure.

When adding WebClass behavior:

- Extend the existing `dendai_skills.webclass` and `dendai_skills.webclass_cli` flow unless the user asks for a different design.
- Run and test commands through the repository virtual environment, for example `.venv/bin/python -m unittest discover -s tests` and `.venv/bin/dendai-webclass ...`. Avoid `conda`, global `python`, global `pip`, or global `dendai-webclass`.
- If the task is being run from another workspace, call the canonical CLI at `/Users/med/Documents/develop/app/product/dendai-skills/.venv/bin/dendai-webclass` and pass paths with `--env`, `--output`, `--pdf-dir`, and `--markdown-dir`.
- Do not write one-off WebClass login scripts into another workspace. If the CLI cannot do what is needed, update this repository's CLI first, then run it.
- Preserve current JSON fields where possible; add new fields rather than breaking existing output.
- Keep PDF and Markdown generation opt-in. Detail scraping should still work without downloading files.
- Add or update focused tests for parser behavior; avoid tests that require live credentials.
- Do not commit, print, or transform `.env` values into docs, fixtures, or logs.

## Environment

Read credentials from `.env` or process environment with these primary keys:

```text
LOGIN_URL=https://els.sa.dendai.ac.jp/webclass/login.php
NUMBER=<student-number>
PASSWORD=<password>
```

The code may keep compatibility aliases, but user-facing examples should use `LOGIN_URL`, `NUMBER`, and `PASSWORD`.

Never print credential values. It is fine to print key names and whether required values are present.

The skill includes `assets/.env.example` as a safe template. For setup, copy that template to the target repository's `.env` and fill in the real values locally. Do not copy the real `.env` into the skill directory or commit it.

For existing workspaces that already have a real `.env`, leave it there and pass it explicitly:

```bash
/Users/med/Documents/develop/app/product/dendai-skills/.venv/bin/dendai-webclass \
  --env /Users/med/Documents/university/.env \
  --output /Users/med/Documents/university/webclass-details.json
```

It is acceptable to check that required keys exist by name. It is not acceptable to print or copy the values.

## Expected Flow

The normal navigation is:

```text
login.html -> home.html -> lesson.html -> detail pages
detail pages: document-detail.html, test-detail.html, report-like pages when present
document execution pages may lead to frames and embedded PDFs
```

Implementation should:

- Login with a persistent `requests.Session`.
- Parse the login form instead of hardcoding hidden token values.
- Post `username=<NUMBER>`, `val=<PASSWORD>`, and preserve hidden inputs such as `token`, `language`, and `useragent`.
- Follow WebClass JavaScript redirects such as `window.location.href=...` and `window.top.location.href=...`.
- Extract course links from the post-login home page, then enter each course before using course-specific content URLs.
- Avoid reusing saved `acs_` URLs across sessions; stale `acs_` values can redirect to logout.
- Treat saved HTML examples as temporary fixtures only; do not keep real user pages in the repo unless the user explicitly asks and sensitive data has been removed.

## Detail Extraction

For `lesson.html` style pages:

- Each `section.cl-contentsList_listGroupItem` is one content item.
- Prefer `data-contents-id`, `data-contents-name`, `data-end-date`, category labels, and the visible `利用可能期間`.
- Capture `詳細`, `利用履歴`, and executable `do_contents.php` links when present.

For detail pages:

- Title is usually `h3.page-header`.
- Kind is usually in text like `種類 : 資料` or `種類 : 自習`.
- Main fields are `.contentsInfoListItem` pairs of `.contentsInfoListLabel` and `.contentsInfoListData`.
- Deadlines often appear under labels such as `日時制限`; preserve the original Japanese label and value in JSON.

## PDF Handling

Only attempt PDF discovery when explicitly requested, for example:

```bash
.venv/bin/dendai-webclass --download-pdfs --pdf-dir data/pdfs
```

Use MarkItDown conversion when Markdown text is requested:

```bash
.venv/bin/dendai-webclass --convert-pdf-md --pdf-dir data/pdfs --markdown-dir data/markdown
```

Document pages may use nested `frame` or `iframe` pages. Crawl a small bounded depth and collect URLs whose path ends with `.pdf`. Ignore PDF viewer help links or generic URLs that merely contain the word `pdf`.

When downloading PDFs:

- Use the same authenticated session.
- Save under `data/pdfs/`.
- Include `pdf_urls`, local `pdf_files`, and when converted, local `md_files` in JSON.
- Do not treat absence of PDFs as a fatal error; many materials are not PDF-backed.
