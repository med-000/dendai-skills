from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .env import getenv_any, load_dotenv
from .webclass import WebClassClient, WebClassCredentials, save_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dendai-webclass",
        description="Login to WebClass, collect lesson detail pages, and save JSON.",
    )
    parser.add_argument("--env", default=".env", help="Path to .env file. Defaults to .env.")
    parser.add_argument(
        "--output",
        default="data/webclass-details.json",
        help="JSON output path. Defaults to data/webclass-details.json.",
    )
    parser.add_argument("--max-courses", type=int, help="Limit the number of courses to scrape.")
    parser.add_argument(
        "--download-pdfs",
        action="store_true",
        help="Try to discover PDF URLs from document execution pages.",
    )
    parser.add_argument(
        "--pdf-dir",
        default="data/pdfs",
        help="Directory for downloaded PDFs when --download-pdfs is set.",
    )
    parser.add_argument(
        "--convert-pdf-md",
        action="store_true",
        help="Convert downloaded PDFs to Markdown with markitdown.",
    )
    parser.add_argument(
        "--markdown-dir",
        default="data/markdown",
        help="Directory for Markdown files when --convert-pdf-md is set.",
    )
    parser.add_argument("--timeout", type=float, default=15.0, help="HTTP timeout seconds.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_dotenv(Path(args.env))

    login_url = getenv_any("WEBCLASS_URL", "DENDAI_WEBCLASS_URL", "LOGIN_URL")
    student_id = getenv_any(
        "NUMBER",
        "WEBCLASS_STUDENT_ID",
        "WEBCLASS_USERNAME",
        "STUDENT_ID",
        "USERNAME",
    )
    password = getenv_any("WEBCLASS_PASSWORD", "PASSWORD")

    missing = [
        name
        for name, value in {
            "LOGIN_URL": login_url,
            "NUMBER": student_id,
            "PASSWORD": password,
        }.items()
        if not value
    ]
    if missing:
        print(f"error: missing env values: {', '.join(missing)}", file=sys.stderr)
        return 2

    client = WebClassClient(
        WebClassCredentials(
            login_url=login_url,
            student_id=student_id,
            password=password,
        ),
        timeout=args.timeout,
    )

    try:
        result = client.scrape(
            max_courses=args.max_courses,
            download_pdfs=args.download_pdfs or args.convert_pdf_md,
            pdf_dir=Path(args.pdf_dir),
            convert_pdf_markdown=args.convert_pdf_md,
            markdown_dir=Path(args.markdown_dir),
        )
        save_result(result, Path(args.output))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    content_count = sum(len(course.contents) for course in result.courses)
    print(f"saved {content_count} contents from {len(result.courses)} courses to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
