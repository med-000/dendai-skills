from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class ScrapeConfig:
    source: str
    selector: str = "body"
    attr: str | None = None
    limit: int | None = None
    timeout: float = 10.0


@dataclass(frozen=True)
class ScrapedItem:
    index: int
    text: str
    value: str | None = None
    html: str | None = None


@dataclass(frozen=True)
class ScrapeResult:
    source: str
    selector: str
    attr: str | None
    scraped_at: str
    items: list[ScrapedItem]


def scrape(config: ScrapeConfig) -> ScrapeResult:
    html = load_html(config.source, config.timeout)
    soup = BeautifulSoup(html, "html.parser")
    elements = soup.select(config.selector)

    if config.limit is not None:
        elements = elements[: config.limit]

    items = [
        ScrapedItem(
            index=index,
            text=element.get_text(" ", strip=True),
            value=element.get(config.attr) if config.attr else None,
            html=str(element),
        )
        for index, element in enumerate(elements)
    ]

    return ScrapeResult(
        source=config.source,
        selector=config.selector,
        attr=config.attr,
        scraped_at=datetime.now(UTC).isoformat(),
        items=items,
    )


def scrape_to_file(config: ScrapeConfig, output_path: Path) -> ScrapeResult:
    result = scrape(config)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def load_html(source: str, timeout: float) -> str:
    if _is_url(source):
        response = requests.get(
            source,
            headers={"User-Agent": "dendai-skills/0.1 (+https://example.invalid)"},
            timeout=timeout,
        )
        response.raise_for_status()
        return response.text

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"source file not found: {source}")
    return path.read_text(encoding="utf-8")


def _is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
