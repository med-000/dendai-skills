---
name: dendai-skills
description: Build or extend the dendai-skills Python scraper, including BeautifulSoup JSON scraping, WebClass login/detail collection, PDF download, and Markdown conversion.
---

# Dendai Skills

Use this skill when the user works on the `dendai-skills` Python scraping tooling, especially BeautifulSoup JSON scraping or Tokyo Denki University WebClass collection.

This skill is not a general permission to restructure a project. It should make the smallest practical change needed for the user's current request.

## Operating Guardrails

- Before editing, inspect the existing files and follow the current repository structure, package names, command names, tests, and dependency style.
- In this repository, run Python commands through the repository virtual environment: `.venv/bin/python`, `.venv/bin/dendai-scrape`, and `.venv/bin/dendai-webclass`. Do not use `conda`, `python`, `pip`, or globally installed entry points unless the user explicitly asks to change environments.
- If `.venv` is missing or broken, recreate it with `.venv/bin/python` unavailable only after checking the current setup; then install the project with `.venv/bin/python -m pip install .`.
- When using this skill from another folder, prefer the canonical installed tool in `/Users/med/Documents/develop/app/product/dendai-skills/.venv/bin/`. Do not create ad-hoc scripts in the target folder just to perform WebClass login or scraping.
- Do not rename, split, merge, delete, or reorganize skills, packages, folders, commands, or modules unless the user explicitly asks for that specific structural change.
- Do not replace an existing application with this repository's starter shape. Treat the starter shape below as context for this repo, not a migration plan for other repos.
- Do not create a new scraper framework, scheduler, database layer, browser automation stack, or plugin/skill layout unless the user explicitly asks for it.
- Keep edits scoped to scraping, parsing, JSON output, PDF download, Markdown conversion, tests, or docs directly related to the request.
- If the user asks to use this skill in another project, adapt to that project's existing conventions instead of copying this repository wholesale.
- If credentials, live login, or external downloads are involved, use `.env` or environment variables and avoid printing secret values.
- Never copy a real `.env` file into a skill, repository fixture, docs, or shared artifact. Use `assets/.env.example` as the template and let the user fill real values in the target repo's local `.env`.
- Real secrets should live in the local project or data workspace that owns the task, such as `/Users/med/Documents/university/.env`; pass that file with `--env /path/to/.env` instead of moving the secret into this skill.
- When unsure whether a change is structural or destructive, stop and ask before making it.

## External Use Pattern

If the user wants to fetch WebClass materials into another directory, run the existing CLI from this repository and point outputs at the target directory. Do not inspect or modify the target project more than needed to choose output paths.

```bash
/Users/med/Documents/develop/app/product/dendai-skills/.venv/bin/dendai-webclass \
  --env /Users/med/Documents/university/.env \
  --output /Users/med/Documents/university/webclass-details.json
```

Forbidden in this mode unless explicitly requested:

- `conda run ...`
- global `python`, global `pip`, or global `dendai-webclass`
- `curl`-based reimplementation of the login flow
- temporary scraper scripts in the target directory, such as `tools/fetch_*.py`
- reading or printing real `.env` values

## Defaults

- Prefer a compact CLI first: input URL or local HTML, explicit extraction targets, JSON output path, and a small typed core module.
- Keep extraction logic separate from command-line parsing so site-specific parsing can be added without rewriting the app.
- Save JSON with UTF-8 and `ensure_ascii=False`.
- Include source URL/path, scrape timestamp, and extracted items in the output.
- Use `requests` for simple HTTP fetches and `BeautifulSoup(..., "html.parser")` unless the project already uses another parser.
- Keep secrets in `.env` or process environment; never print credential values in logs or final answers.

## Boundaries

- Do not bypass robots, paywalls, login gates, or rate limits.
- Follow ordinary redirects and simple JavaScript location redirects when they are part of the normal logged-in flow.
- For pages whose content is rendered client-side by JavaScript, recommend Playwright or browser automation instead of forcing BeautifulSoup.
- Ask before adding database storage, scheduled scraping, proxy rotation, or aggressive crawling.

## Repository Shape

```text
pyproject.toml
dendai_skills/
  cli.py
  scraper.py
data/
```

This is the current repository's shape. Preserve it unless the user asks to change it.

For this repository's generic command:

```bash
.venv/bin/dendai-scrape <url-or-html-file> --selector "<css-selector>" --output data/result.json
```

## Dendai WebClass Project

When working on Tokyo Denki University WebClass scraping in this repo, read [references/webclass.md](references/webclass.md). It contains the expected `.env` keys, page flow, redirect quirks, and PDF handling rules.
