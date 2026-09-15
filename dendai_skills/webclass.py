from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag


DEFAULT_USER_AGENT = "dendai-skills/0.1"


@dataclass(frozen=True)
class WebClassCredentials:
    login_url: str
    student_id: str
    password: str


@dataclass(frozen=True)
class WebClassDetail:
    title: str | None
    kind: str | None
    course_title: str | None
    url: str
    fields: dict[str, str]
    links: dict[str, str]


@dataclass(frozen=True)
class WebClassContent:
    content_id: str | None
    name: str | None
    category: str | None
    availability: str | None
    end_timestamp: int | None
    detail_url: str | None
    execute_url: str | None
    history_url: str | None
    detail: WebClassDetail | None = None
    pdf_urls: list[str] = field(default_factory=list)
    pdf_files: list[str] = field(default_factory=list)
    md_files: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class WebClassCourse:
    name: str
    url: str
    contents: list[WebClassContent]


@dataclass(frozen=True)
class WebClassResult:
    scraped_at: str
    login_url: str
    courses: list[WebClassCourse]


class WebClassClient:
    def __init__(self, credentials: WebClassCredentials, timeout: float = 15.0) -> None:
        self.credentials = credentials
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": DEFAULT_USER_AGENT})

    def login(self) -> str:
        response = self.session.get(self.credentials.login_url, timeout=self.timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        form = soup.select_one("form[name='login']") or soup.select_one("form")
        if not isinstance(form, Tag):
            raise RuntimeError("login form was not found")

        action = form.get("action") or self.credentials.login_url
        post_url = urljoin(response.url, str(action))
        payload = _form_payload(form)
        payload.update(
            {
                "username": self.credentials.student_id,
                "val": self.credentials.password,
                "login": payload.get("login", "Login"),
            }
        )

        logged_in = self.session.post(post_url, data=payload, timeout=self.timeout)
        logged_in.raise_for_status()
        if _looks_like_login_page(logged_in.text):
            raise RuntimeError("login failed or WebClass returned the login page again")
        return _javascript_redirect_url(logged_in.text, logged_in.url) or logged_in.url

    def get(self, url: str) -> requests.Response:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        for _ in range(5):
            redirect_url = _javascript_redirect_url(response.text, response.url)
            if not redirect_url:
                return response
            response = self.session.get(redirect_url, timeout=self.timeout)
            response.raise_for_status()
        raise RuntimeError(f"too many JavaScript redirects: {url}")

    def scrape(
        self,
        max_courses: int | None = None,
        download_pdfs: bool = False,
        pdf_dir: Path = Path("data/pdfs"),
        convert_pdf_markdown: bool = False,
        markdown_dir: Path = Path("data/markdown"),
    ) -> WebClassResult:
        home_url = self.login()
        home = self.get(home_url)
        base_url = home.url

        courses = []
        for course_name, course_url in _extract_course_links(home.text, base_url):
            if max_courses is not None and len(courses) >= max_courses:
                break
            course_page = self.get(course_url)
            contents = self.scrape_course(
                course_page.url,
                course_page.text,
                download_pdfs,
                pdf_dir,
                convert_pdf_markdown,
                markdown_dir,
            )
            courses.append(WebClassCourse(name=course_name, url=course_page.url, contents=contents))

        return WebClassResult(
            scraped_at=datetime.now(UTC).isoformat(),
            login_url=self.credentials.login_url,
            courses=courses,
        )

    def scrape_course(
        self,
        course_url: str,
        course_html: str,
        download_pdfs: bool = False,
        pdf_dir: Path = Path("data/pdfs"),
        convert_pdf_markdown: bool = False,
        markdown_dir: Path = Path("data/markdown"),
    ) -> list[WebClassContent]:
        contents = []
        for content in parse_lesson_contents(course_html, course_url):
            detail = None
            pdf_urls: list[str] = []
            if content.detail_url:
                detail_response = self.get(content.detail_url)
                detail = parse_detail_page(detail_response.text, detail_response.url)
            if download_pdfs and content.execute_url:
                pdf_urls = self.find_pdf_urls(content.execute_url)
            pdf_files = self.download_pdf_urls(pdf_urls, content.content_id, pdf_dir) if pdf_urls else []
            md_files = convert_pdf_files_to_markdown(pdf_files, markdown_dir) if convert_pdf_markdown else []

            contents.append(
                WebClassContent(
                    content_id=content.content_id,
                    name=content.name,
                    category=content.category,
                    availability=content.availability,
                    end_timestamp=content.end_timestamp,
                    detail_url=content.detail_url,
                    execute_url=content.execute_url,
                    history_url=content.history_url,
                    detail=detail,
                    pdf_urls=pdf_urls,
                    pdf_files=pdf_files,
                    md_files=md_files,
                )
            )
        return contents

    def find_pdf_urls(self, execute_url: str) -> list[str]:
        response = self.get(execute_url)
        return sorted(set(self._crawl_pdf_urls(response.text, response.url)))

    def download_pdf_urls(
        self,
        pdf_urls: Iterable[str],
        content_id: str | None,
        pdf_dir: Path,
    ) -> list[str]:
        pdf_dir.mkdir(parents=True, exist_ok=True)
        saved = []
        for index, url in enumerate(pdf_urls, start=1):
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            if "pdf" not in response.headers.get("content-type", "").lower():
                continue

            filename = _pdf_filename(url, content_id, index)
            path = pdf_dir / filename
            path.write_bytes(response.content)
            saved.append(str(path))
        return saved

    def _crawl_pdf_urls(self, html: str, base_url: str, depth: int = 0) -> list[str]:
        if depth >= 4:
            return []

        urls = extract_pdf_candidates(html, base_url)
        for frame_url in extract_frame_urls(html, base_url):
            try:
                frame_response = self.get(frame_url)
            except requests.RequestException:
                continue
            urls.extend(self._crawl_pdf_urls(frame_response.text, frame_response.url, depth + 1))

        return urls


def parse_lesson_contents(html: str, base_url: str) -> list[WebClassContent]:
    soup = BeautifulSoup(html, "html.parser")
    contents: list[WebClassContent] = []

    for section in soup.select("section.cl-contentsList_listGroupItem"):
        if not isinstance(section, Tag):
            continue

        links = _links_by_text(section, base_url)
        name = section.get("data-contents-name") or _content_name(section)
        category_tag = section.select_one(".cl-contentsList_categoryLabel")
        availability = _labeled_value(section, "利用可能期間")
        execute_url = _first_do_contents_url(section, base_url)

        contents.append(
            WebClassContent(
                content_id=_string_or_none(section.get("data-contents-id")),
                name=_string_or_none(name),
                category=_text_or_none(category_tag),
                availability=availability,
                end_timestamp=_int_or_none(section.get("data-end-date")),
                detail_url=links.get("詳細"),
                execute_url=execute_url,
                history_url=links.get("利用回数") or _find_link_containing(section, "history", base_url),
            )
        )

    return contents


def parse_detail_page(html: str, url: str) -> WebClassDetail:
    soup = BeautifulSoup(html, "html.parser")
    fields: dict[str, str] = {}

    for item in soup.select(".contentsInfoListItem"):
        label = _text_or_none(item.select_one(".contentsInfoListLabel"))
        value = _text_or_none(item.select_one(".contentsInfoListData"))
        if label:
            fields[label] = value or ""

    links = _links_by_text(soup, url)
    title = _text_or_none(soup.select_one("h3.page-header"))
    kind = _normalize_kind(_text_or_none(soup.select_one("h3.page-header + p")))
    course = _text_or_none(soup.select_one(".course-name"))

    return WebClassDetail(
        title=title,
        kind=kind,
        course_title=course,
        url=url,
        fields=fields,
        links=links,
    )


def extract_frame_urls(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for tag in soup.select("frame[src], iframe[src]"):
        src = tag.get("src")
        if src:
            urls.append(urljoin(base_url, str(src)))
    return urls


def extract_pdf_candidates(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for tag in soup.select("a[href], iframe[src], frame[src], embed[src], object[data]"):
        raw_url = tag.get("href") or tag.get("src") or tag.get("data")
        if not raw_url:
            continue
        url = urljoin(base_url, str(raw_url))
        parsed = urlparse(url)
        if parsed.path.lower().endswith(".pdf"):
            urls.append(url)
    return urls


def save_result(result: WebClassResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def convert_pdf_files_to_markdown(pdf_files: Iterable[str], markdown_dir: Path) -> list[str]:
    from markitdown import MarkItDown

    markdown_dir.mkdir(parents=True, exist_ok=True)
    converter = MarkItDown()
    saved = []

    for pdf_file in pdf_files:
        pdf_path = Path(pdf_file)
        result = converter.convert(pdf_path)
        markdown_path = markdown_dir / f"{pdf_path.stem}.md"
        markdown_path.write_text(result.markdown, encoding="utf-8")
        saved.append(str(markdown_path))

    return saved


def _pdf_filename(url: str, content_id: str | None, index: int) -> str:
    basename = Path(urlparse(url).path).name
    if not basename.lower().endswith(".pdf"):
        basename = f"{index}.pdf"
    prefix = re.sub(r"[^a-zA-Z0-9_-]+", "_", content_id or "content").strip("_")
    return f"{prefix}-{index:02d}-{basename}"


def _extract_course_links(html: str, base_url: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    courses: list[tuple[str, str]] = []
    seen = set()

    for link in soup.select("a[href*='/webclass/course.php/'][href*='/login']"):
        href = link.get("href")
        if not href:
            continue
        url = urljoin(base_url, str(href))
        if url in seen:
            continue
        seen.add(url)
        name = _clean_course_name(link.get_text(" ", strip=True))
        courses.append((name or url, url))

    return courses


def _form_payload(form: Tag) -> dict[str, str]:
    payload = {}
    for control in form.select("input[name], textarea[name], select[name]"):
        if not isinstance(control, Tag):
            continue
        name = control.get("name")
        if not name:
            continue
        payload[str(name)] = str(control.get("value") or "")
    return payload


def _looks_like_login_page(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    return bool(soup.select_one("form[name='login'] #username"))


def _javascript_redirect_url(html: str, base_url: str) -> str | None:
    match = re.search(r"(?:window(?:\.top)?|top)?\.?location\.href\s*=\s*['\"]([^'\"]+)['\"]", html)
    if not match:
        return None
    return urljoin(base_url, match.group(1).replace("\\/", "/"))


def _links_by_text(root: Tag | BeautifulSoup, base_url: str) -> dict[str, str]:
    links: dict[str, str] = {}
    for link in root.select("a[href]"):
        text = link.get_text(" ", strip=True)
        href = link.get("href")
        if text and href:
            links.setdefault(text, urljoin(base_url, str(href)))
    return links


def _first_do_contents_url(root: Tag, base_url: str) -> str | None:
    for link in root.select("a[href*='do_contents.php']"):
        href = link.get("href")
        if href:
            return urljoin(base_url, str(href))
    return None


def _find_link_containing(root: Tag, needle: str, base_url: str) -> str | None:
    for link in root.select("a[href]"):
        href = str(link.get("href") or "")
        if needle in href:
            return urljoin(base_url, href)
    return None


def _content_name(section: Tag) -> str | None:
    heading = section.select_one(".cm-contentsList_contentName")
    if not heading:
        return None
    marker = heading.select_one(".cl-contentsList_new")
    if marker:
        marker.decompose()
    return heading.get_text(" ", strip=True)


def _labeled_value(section: Tag, label_text: str) -> str | None:
    for item in section.select(".cm-contentsList_contentDetailListItem"):
        label = _text_or_none(item.select_one(".cm-contentsList_contentDetailListItemLabel"))
        if label == label_text:
            return _text_or_none(item.select_one(".cm-contentsList_contentDetailListItemData"))
    return None


def _normalize_kind(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(r"種類\s*[:：]\s*(.+)", text)
    return match.group(1).strip() if match else text


def _clean_course_name(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("»", "")).strip()


def _text_or_none(tag: Tag | None) -> str | None:
    if not tag:
        return None
    text = tag.get_text(" ", strip=True)
    return text or None


def _string_or_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int_or_none(value: object) -> int | None:
    try:
        number = int(str(value))
    except (TypeError, ValueError):
        return None
    return number or None
