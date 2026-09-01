"""HTTP fetching and clean-DOM / clean-text extraction.

Produces a :class:`PageSnapshot` — the single, immutable-ish input consumed
by all three audit pillars. Uses Trafilatura for boilerplate-stripped main
content when available, with a BeautifulSoup fallback so the extractor works
in any environment.

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

import html as html_lib
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from sage_audit.utils.text import count_tokens, count_words

logger = logging.getLogger("sage_audit.extractor")

try:  # Trafilatura is a hard dependency in requirements, but stay defensive.
    import trafilatura  # type: ignore
except Exception:  # pragma: no cover - exercised only without trafilatura
    trafilatura = None  # type: ignore[assignment]

USER_AGENT = "sage-audit/1.0 (+https://molavi.pro; SAGE Audit Bot)"
DEFAULT_TIMEOUT = 20.0

HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")
BOILERPLATE_TAGS = (
    "script", "style", "noscript", "template", "svg", "nav",
    "footer", "header", "aside", "form", "button", "select",
)


class FetchError(RuntimeError):
    """Raised when a target URL cannot be retrieved."""


@dataclass
class Section:
    """A heading-anchored block of body text (used by AEO + GEO pillars)."""

    heading: Optional[str]
    level: int
    text: str
    word_count: int


@dataclass
class PageSnapshot:
    """Everything an auditor needs to know about one page."""

    # --- transport ---
    url: str
    final_url: str = ""
    status_code: int = 0  # 0 == offline / raw HTML input
    headers: dict[str, str] = field(default_factory=dict)  # keys lower-cased
    fetch_ms: float = 0.0
    robots_txt: Optional[str] = None

    # --- raw material ---
    html: str = ""
    text: str = ""  # boilerplate-stripped main content

    # --- head signals ---
    title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_robots: Optional[str] = None
    canonical: Optional[str] = None
    language: Optional[str] = None
    open_graph: dict[str, str] = field(default_factory=dict)
    meta: dict[str, str] = field(default_factory=dict)

    # --- body structure ---
    headings: list[tuple[int, str]] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)
    json_ld: list[Any] = field(default_factory=list)
    json_ld_errors: int = 0
    images_total: int = 0
    images_without_alt: int = 0
    links_internal: int = 0
    links_external: int = 0

    # --- quantitative ---
    word_count: int = 0
    token_count: int = 0
    text_to_code_ratio: float = 0.0

    def header(self, name: str) -> Optional[str]:
        """Case-insensitive HTTP header lookup."""

        return self.headers.get(name.lower())


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def ensure_url(target: str) -> str:
    """Normalize a user-supplied target into an absolute URL."""

    target = (target or "").strip()
    if not target:
        raise FetchError("Empty URL.")
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", target):
        target = "https://" + target
    return target


def fetch_url(
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
    session: Optional[requests.Session] = None,
) -> tuple[int, dict[str, str], str, str, float]:
    """Fetch ``url``; returns (status, headers, html, final_url, elapsed_ms)."""

    http = session or requests.Session()
    http.headers.setdefault("User-Agent", USER_AGENT)
    started = time.perf_counter()
    try:
        response = http.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
    except requests.RequestException as exc:
        raise FetchError(f"Could not fetch {url!r}: {exc}") from exc
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    headers = {str(k).lower(): str(v) for k, v in response.headers.items()}
    return response.status_code, headers, response.text or "", str(response.url), elapsed_ms


def fetch_robots_txt(
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
    session: Optional[requests.Session] = None,
) -> Optional[str]:
    """Fetch the site's robots.txt; returns None when missing/unreachable."""

    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    http = session or requests.Session()
    try:
        response = http.get(robots_url, timeout=max(5.0, timeout / 2))
    except requests.RequestException as exc:  # pragma: no cover - network dependent
        logger.debug("robots.txt fetch failed for %s: %s", robots_url, exc)
        return None
    if response.status_code == 200 and response.text:
        return response.text
    return None


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _extract_json_ld(soup: BeautifulSoup) -> tuple[list[Any], int]:
    """Parse every <script type="application/ld+json"> block, tolerating
    HTML-entity-escaped payloads. Returns (blocks, parse_error_count)."""

    blocks: list[Any] = []
    errors = 0
    for tag in soup.find_all("script", attrs={"type": re.compile(r"ld\+json", re.I)}):
        raw = (tag.string or tag.get_text() or "").strip()
        if not raw:
            continue
        try:
            blocks.append(json.loads(raw))
        except json.JSONDecodeError:
            cleaned = html_lib.unescape(raw)
            try:
                blocks.append(json.loads(cleaned))
            except json.JSONDecodeError:
                errors += 1
                logger.debug("Unparseable JSON-LD block skipped (%d bytes)", len(raw))
    return blocks, errors


def _extract_main_text(html: str) -> str:
    """Boilerplate-stripped main content (Trafilatura first, BS4 fallback)."""

    if trafilatura is not None:
        try:
            extracted = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=False,
                favor_recall=True,
            )
            if extracted and len(extracted.split()) >= 30:
                return extracted.strip()
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("trafilatura extraction failed, falling back: %s", exc)

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(list(BOILERPLATE_TAGS)):
        tag.decompose()
    lines = [line.strip() for line in soup.get_text("\n").splitlines() if line.strip()]
    return "\n".join(lines)


def _extract_sections(html: str) -> list[Section]:
    """Group body copy under their nearest preceding heading.

    Prefers <main>/<article> containers to skip chrome; falls back to body.
    """

    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("main") or soup.find("article") or soup.body or soup

    sections: list[Section] = []
    current_heading: Optional[str] = None
    current_level = 0
    buffer: list[str] = []

    def flush() -> None:
        if current_heading is None and not buffer:
            return
        text = " ".join(buffer).strip()
        if not text and current_heading is None:
            return
        sections.append(
            Section(
                heading=current_heading,
                level=current_level,
                text=text,
                word_count=count_words(text),
            )
        )

    for element in container.find_all(list(HEADING_TAGS) + ["p", "li", "blockquote", "pre"]):
        if element.find_parent(list(BOILERPLATE_TAGS)):
            continue
        text = element.get_text(" ", strip=True)
        if not text:
            continue
        if element.name in HEADING_TAGS:
            flush()
            buffer = []
            current_heading = text
            current_level = int(element.name[1])
        else:
            if element.find_parent(list(HEADING_TAGS)):
                continue  # heading already handled
            buffer.append(text)
    flush()

    # Merge a fragmentary leading section (pre-heading copy) into the first
    # properly-headed section when it is too small to stand alone.
    if (
        len(sections) >= 2
        and sections[0].heading is None
        and sections[0].word_count < 25
    ):
        lead = sections.pop(0)
        sections[0].text = f"{lead.text} {sections[0].text}".strip()
        sections[0].word_count = count_words(sections[0].text)
    return sections


def parse_snapshot(
    url: str,
    html: str,
    *,
    status_code: int = 0,
    headers: Optional[dict[str, str]] = None,
    final_url: str = "",
    robots_txt: Optional[str] = None,
    fetch_ms: float = 0.0,
) -> PageSnapshot:
    """Build a :class:`PageSnapshot` from raw HTML (never touches network)."""

    soup = BeautifulSoup(html or "", "html.parser")

    title: Optional[str] = None
    if soup.title and soup.title.string:
        title = soup.title.string.strip() or None

    meta: dict[str, str] = {}
    for tag in soup.find_all("meta"):
        key = (tag.get("name") or tag.get("property") or "").strip().lower()
        content = tag.get("content")
        if key and content and key not in meta:
            meta[key] = content.strip()
    open_graph = {key[3:]: value for key, value in meta.items() if key.startswith("og:")}

    canonical: Optional[str] = None
    link = soup.find("link", rel=lambda v: v and "canonical" in v)
    if link and link.get("href"):
        canonical = str(link["href"]).strip()

    language: Optional[str] = None
    if soup.html and soup.html.get("lang"):
        language = str(soup.html["lang"]).strip()

    json_ld, json_ld_errors = _extract_json_ld(soup)

    headings = [
        (int(tag.name[1]), tag.get_text(" ", strip=True))
        for tag in soup.find_all(list(HEADING_TAGS))
        if tag.get_text(strip=True)
    ]

    images = soup.find_all("img")
    images_total = len(images)
    images_without_alt = sum(
        1 for img in images if img.get("alt") is None or not str(img.get("alt", "")).strip()
    )

    base_netloc = urlparse(final_url or url).netloc
    links_internal = 0
    links_external = 0
    for anchor in soup.find_all("a", href=True):
        href = str(anchor["href"]).strip()
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        target = urlparse(href)
        if not target.netloc or target.netloc == base_netloc:
            links_internal += 1
        else:
            links_external += 1

    # Visible-text length vs. markup length -> text-to-code ratio.
    clone = BeautifulSoup(html or "", "html.parser")
    for tag in clone(["script", "style", "noscript", "template"]):
        tag.decompose()
    document_text = clone.get_text(" ").strip()
    text_to_code = round(len(document_text) / max(len(html or ""), 1), 4)

    main_text = _extract_main_text(html or "")
    sections = _extract_sections(html or "")

    return PageSnapshot(
        url=url,
        final_url=final_url,
        status_code=status_code,
        headers={str(k).lower(): str(v) for k, v in (headers or {}).items()},
        fetch_ms=round(fetch_ms, 2),
        robots_txt=robots_txt,
        html=html or "",
        text=main_text,
        title=title,
        meta_description=meta.get("description"),
        meta_robots=meta.get("robots"),
        canonical=canonical,
        language=language,
        open_graph=open_graph,
        meta=meta,
        headings=headings,
        sections=sections,
        json_ld=json_ld,
        json_ld_errors=json_ld_errors,
        images_total=images_total,
        images_without_alt=images_without_alt,
        links_internal=links_internal,
        links_external=links_external,
        word_count=count_words(main_text),
        token_count=count_tokens(main_text),
        text_to_code_ratio=text_to_code,
    )
