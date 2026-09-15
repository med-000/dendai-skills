from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .scraper import ScrapeConfig, scrape_to_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dendai-scrape",
        description="Scrape HTML with BeautifulSoup and save extracted data as JSON.",
    )
    parser.add_argument("source", help="URL or local HTML file path.")
    parser.add_argument(
        "--selector",
        default="body",
        help="CSS selector to extract. Defaults to body.",
    )
    parser.add_argument(
        "--attr",
        help="Optional attribute name to extract from each matched element, e.g. href.",
    )
    parser.add_argument(
        "--output",
        default="data/scraped.json",
        help="JSON output path. Defaults to data/scraped.json.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of matched elements to save.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP timeout seconds. Defaults to 10.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    config = ScrapeConfig(
        source=args.source,
        selector=args.selector,
        attr=args.attr,
        limit=args.limit,
        timeout=args.timeout,
    )

    try:
        result = scrape_to_file(config, Path(args.output))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"saved {len(result.items)} items to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

