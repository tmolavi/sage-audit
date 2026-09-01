"""Pillar 1 — Classical Technical SEO.

Covers clean-DOM hygiene, metadata, canonicalization, security/cache HTTP
signals and — critically for the AI-search era — the site's robots.txt
policy toward AI crawlers (GPTBot, PerplexityBot, ClaudeBot,
Google-Extended, Amazonbot, Applebot-Extended).

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

import time
from urllib.parse import urlparse

from sage_audit.models import Finding, PillarReport, Status, finalize_pillar
from sage_audit.utils.extractor import PageSnapshot

#: AI crawlers whose robots.txt policy decides AI-search visibility.
AI_CRAWLERS: tuple[str, ...] = (
    "GPTBot",
    "PerplexityBot",
    "ClaudeBot",
    "Google-Extended",
    "Amazonbot",
    "Applebot-Extended",
)

#: Response headers scored in the security check.
SECURITY_HEADERS: tuple[str, ...] = (
    "strict-transport-security",
    "content-security-policy",
    "x-content-type-options",
    "x-frame-options",
)

#: Response headers scored in the cache check.
CACHE_HEADERS: tuple[str, ...] = (
    "cache-control",
    "etag",
    "last-modified",
    "expires",
)


# ---------------------------------------------------------------------------
# robots.txt parsing (pure functions — unit-testable without networking)
# ---------------------------------------------------------------------------

def parse_robots(robots_txt: str) -> dict[str, list[tuple[str, str]]]:
    """Parse robots.txt into {user_agent: [(directive, value), ...]}.

    Consecutive ``User-agent`` lines before a rule line form one group; keys
    and directives are lower-cased. Sitemaps and crawl-delay are ignored by
    design (they do not affect allow/block verdicts).
    """

    groups: dict[str, list[tuple[str, str]]] = {}
    agents: list[str] = []
    saw_rule = False
    for raw_line in robots_txt.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower().replace("_", "-")
        value = value.strip()
        if key == "user-agent":
            if saw_rule:
                agents = []
                saw_rule = False
            agents.append(value.lower())
        elif key in ("allow", "disallow"):
            for agent in agents:
                groups.setdefault(agent, []).append((key, value))
            saw_rule = True
    return groups


def ai_crawler_verdicts(
    robots_txt: str, crawlers: tuple[str, ...] = AI_CRAWLERS
) -> dict[str, str]:
    """Return {crawler: 'allowed' | 'blocked'} for each AI crawler.

    A crawler is *blocked* when its most specific group (exact match,
    otherwise ``*``) contains ``Disallow: /`` without a root-level ``Allow``
    override. Anything else — including absence from the file — is *allowed*,
    which matches how the major crawlers interpret the standard.
    """

    groups = parse_robots(robots_txt)
    verdicts: dict[str, str] = {}
    for crawler in crawlers:
        rules = groups.get(crawler.lower())
        if rules is None:
            rules = groups.get("*", [])
        disallows_root = any(directive == "disallow" and value == "/" for directive, value in rules)
        allows_root = any(
            directive == "allow" and value.startswith("/") for directive, value in rules
        )
        verdicts[crawler] = "blocked" if (disallows_root and not allows_root) else "allowed"
    return verdicts


# ---------------------------------------------------------------------------
# The auditor
# ---------------------------------------------------------------------------

class SeoAuditor:
    """Executes all Pillar-1 checks against a :class:`PageSnapshot`."""

    pillar_name = "Pillar 1 — Technical SEO"

    def audit(self, snap: PageSnapshot) -> PillarReport:
        started = time.perf_counter()
        findings = [
            self._check_http_status(snap),
            self._check_https(snap),
            self._check_title(snap),
            self._check_meta_description(snap),
            self._check_canonical(snap),
            self._check_meta_robots(snap),
            self._check_open_graph(snap),
            self._check_h1(snap),
            self._check_language(snap),
            self._check_image_alts(snap),
            self._check_word_count(snap),
            self._check_text_to_code(snap),
            self._check_security_headers(snap),
            self._check_cache_headers(snap),
            self._check_robots_ai_crawlers(snap),
        ]
        metrics = {
            "status_code": snap.status_code,
            "fetch_ms": snap.fetch_ms,
            "word_count": snap.word_count,
            "text_to_code_ratio": snap.text_to_code_ratio,
            "links_internal": snap.links_internal,
            "links_external": snap.links_external,
            "images_total": snap.images_total,
            "images_without_alt": snap.images_without_alt,
            "ai_crawlers": (
                ai_crawler_verdicts(snap.robots_txt) if snap.robots_txt else None
            ),
        }
        return finalize_pillar("seo", self.pillar_name, findings, metrics=metrics, started=started)

    # ------------------------------------------------------------------ #
    # individual checks
    # ------------------------------------------------------------------ #

    def _check_http_status(self, snap: PageSnapshot) -> Finding:
        if snap.status_code == 0:
            return Finding(
                check_id="seo.http_status",
                title="HTTP status",
                status=Status.INFO,
                score=1.0,
                weight=0.0,
                details="Raw HTML input — live transport not evaluated.",
                recommendation="",
            )
        ok = 200 <= snap.status_code < 300
        return Finding(
            check_id="seo.http_status",
            title="HTTP status",
            status=Status.PASS if ok else Status.FAIL,
            score=1.0 if ok else 0.0,
            weight=6.0,
            details=f"GET {snap.final_url or snap.url} → {snap.status_code} "
            f"in {snap.fetch_ms:.0f} ms.",
            recommendation="" if ok else
            f"The page returns HTTP {snap.status_code}; search and answer engines "
            "only index 2xx responses. Fix redirects/errors at the edge.",
        )

    def _check_https(self, snap: PageSnapshot) -> Finding:
        scheme = urlparse(snap.url).scheme
        secure = scheme == "https"
        return Finding(
            check_id="seo.https",
            title="HTTPS transport",
            status=Status.PASS if secure else Status.FAIL,
            score=1.0 if secure else 0.1,
            weight=5.0,
            details=f"URL scheme is '{scheme or 'unknown'}'.",
            recommendation="" if secure else
            "Serve the page over HTTPS; plain HTTP is a negative ranking and "
            "trust signal for both classic and AI search surfaces.",
        )

    def _check_title(self, snap: PageSnapshot) -> Finding:
        title = snap.title or ""
        length = len(title)
        if not title:
            score, details, rec = 0.0, "No <title> element found.", (
                "Add a unique, descriptive <title> (30–60 characters) — it remains the "
                "strongest single on-page relevance signal."
            )
        elif 30 <= length <= 60:
            score, details, rec = 1.0, f"Title is {length} characters: “{title}”.", ""
        elif 10 <= length <= 70:
            score, details, rec = 0.7, f"Title is {length} characters (ideal 30–60).", (
                "Tune the title toward 30–60 characters to avoid truncation in SERPs "
                "and answer-engine citations."
            )
        else:
            score, details, rec = 0.3, f"Title is {length} characters — far outside 30–60.", (
                "Rewrite the title: extremely short/long titles are truncated or "
                "rewritten by Google and ignored by answer engines."
            )
        return Finding(
            check_id="seo.title",
            title="Title tag",
            status=Status.PASS if score == 1.0 else (Status.FAIL if score <= 0.3 else Status.WARN),
            score=score,
            weight=8.0,
            details=details,
            recommendation=rec,
        )

    def _check_meta_description(self, snap: PageSnapshot) -> Finding:
        desc = snap.meta_description or ""
        length = len(desc)
        if not desc:
            score, details, rec = 0.0, "No meta description found.", (
                "Write a 70–160 character meta description — it feeds SERP snippets "
                "and is frequently quoted verbatim by AI answer engines."
            )
        elif 70 <= length <= 160:
            score, details, rec = 1.0, f"Meta description is {length} characters.", ""
        elif 40 <= length <= 200:
            score, details, rec = 0.6, f"Meta description is {length} characters (ideal 70–160).", (
                "Adjust the meta description to 70–160 characters for full snippet display."
            )
        else:
            score, details, rec = 0.3, f"Meta description is {length} characters — outside 70–160.", (
                "Rewrite the meta description between 70 and 160 characters."
            )
        return Finding(
            check_id="seo.meta_description",
            title="Meta description",
            status=Status.PASS if score == 1.0 else (Status.FAIL if score <= 0.3 else Status.WARN),
            score=score,
            weight=6.0,
            details=details,
            recommendation=rec,
        )

    def _check_canonical(self, snap: PageSnapshot) -> Finding:
        canonical = snap.canonical
        if canonical and canonical.startswith(("http://", "https://")):
            return Finding(
                check_id="seo.canonical",
                title="Canonical URL",
                status=Status.PASS,
                score=1.0,
                weight=6.0,
                details=f"canonical → {canonical}",
                recommendation="",
            )
        if canonical:
            return Finding(
                check_id="seo.canonical",
                title="Canonical URL",
                status=Status.WARN,
                score=0.5,
                weight=6.0,
                details=f"Relative canonical “{canonical}”.",
                recommendation="Use an absolute canonical URL (https://…) to remove ambiguity "
                "across crawlers and RAG ingestion pipelines.",
            )
        return Finding(
            check_id="seo.canonical",
            title="Canonical URL",
            status=Status.FAIL,
            score=0.0,
            weight=6.0,
            details="No <link rel=\"canonical\"> found.",
            recommendation="Add a self-referencing absolute canonical tag to consolidate "
            "link equity and prevent duplicate-content splits.",
        )

    def _check_meta_robots(self, snap: PageSnapshot) -> Finding:
        value = (snap.meta_robots or "").lower()
        if "noindex" in value:
            return Finding(
                check_id="seo.meta_robots",
                title="Meta robots directives",
                status=Status.FAIL,
                score=0.0,
                weight=10.0,
                details=f'content="{snap.meta_robots}" contains noindex.',
                recommendation="Remove 'noindex' — the page is explicitly opting out of "
                "Google/Bing indices and most answer engines that reuse them.",
            )
        compact = value.replace(" ", "")
        if "nosnippet" in value or "max-snippet:0" in compact:
            return Finding(
                check_id="seo.meta_robots",
                title="Meta robots directives",
                status=Status.WARN,
                score=0.5,
                weight=10.0,
                details=f'content="{snap.meta_robots}" restricts snippets.',
                recommendation="'nosnippet'/'max-snippet:0' removes the page from featured "
                "snippets and many AI answers; relax it unless intentional.",
            )
        return Finding(
            check_id="seo.meta_robots",
            title="Meta robots directives",
            status=Status.PASS,
            score=1.0,
            weight=10.0,
            details=(f'content="{snap.meta_robots}".' if value else
                     "No meta robots tag — defaults to index,follow."),
            recommendation="",
        )

    def _check_open_graph(self, snap: PageSnapshot) -> Finding:
        required = ("title", "description", "image", "type")
        present = [key for key in required if snap.open_graph.get(key)]
        missing = [key for key in required if key not in present]
        score = len(present) / len(required)
        status = Status.PASS if score == 1.0 else (Status.WARN if score >= 0.5 else Status.FAIL)
        return Finding(
            check_id="seo.open_graph",
            title="Open Graph protocol",
            status=status,
            score=score,
            weight=5.0,
            details=(f"{len(present)}/{len(required)} core og: properties present"
                     + (f"; missing: {', '.join('og:' + m for m in missing)}" if missing else "")),
            recommendation="" if score == 1.0 else
            "Complete og:title, og:description, og:image and og:type — social and AI "
            "surfaces build their citations/cards from these tags.",
        )

    def _check_h1(self, snap: PageSnapshot) -> Finding:
        h1s = [text for level, text in snap.headings if level == 1]
        if len(h1s) == 1:
            return Finding(
                check_id="seo.h1",
                title="H1 heading",
                status=Status.PASS,
                score=1.0,
                weight=5.0,
                details=f"Exactly one H1: “{h1s[0]}”.",
                recommendation="",
            )
        if not h1s:
            return Finding(
                check_id="seo.h1",
                title="H1 heading",
                status=Status.FAIL,
                score=0.2,
                weight=5.0,
                details="No <h1> found on the page.",
                recommendation="Add a single, descriptive <h1> mirroring the page's core entity/query.",
            )
        return Finding(
            check_id="seo.h1",
            title="H1 heading",
            status=Status.WARN,
            score=0.6,
            weight=5.0,
            details=f"{len(h1s)} <h1> elements found.",
            recommendation="Keep exactly one <h1> per page; demote the rest to <h2>.",
        )

    def _check_language(self, snap: PageSnapshot) -> Finding:
        if snap.language:
            return Finding(
                check_id="seo.lang",
                title="Document language",
                status=Status.PASS,
                score=1.0,
                weight=2.0,
                details=f'html lang="{snap.language}".',
                recommendation="",
            )
        return Finding(
            check_id="seo.lang",
            title="Document language",
            status=Status.WARN,
            score=0.5,
            weight=2.0,
            details="No lang attribute on <html>.",
            recommendation='Set <html lang="…"> — it feeds hreflang, TTS and multilingual '
            "answer-engine indexing.",
        )

    def _check_image_alts(self, snap: PageSnapshot) -> Finding:
        if snap.images_total == 0:
            return Finding(
                check_id="seo.image_alts",
                title="Image alt coverage",
                status=Status.INFO,
                score=1.0,
                weight=0.0,
                details="No <img> elements on the page.",
                recommendation="",
            )
        coverage = 1.0 - (snap.images_without_alt / snap.images_total)
        status = Status.PASS if coverage >= 0.9 else (Status.WARN if coverage >= 0.5 else Status.FAIL)
        return Finding(
            check_id="seo.image_alts",
            title="Image alt coverage",
            status=status,
            score=coverage,
            weight=4.0,
            details=f"{snap.images_total - snap.images_without_alt}/{snap.images_total} "
            "images carry alt text.",
            recommendation="" if coverage >= 0.9 else
            "Describe every informative image with alt text — multimodal answer engines "
            "quote alt text when grounding visual claims.",
        )

    def _check_word_count(self, snap: PageSnapshot) -> Finding:
        words = snap.word_count
        if words >= 600:
            score, status, rec = 1.0, Status.PASS, ""
        elif words >= 300:
            score, status, rec = 0.7, Status.WARN, (
                "Main content is on the thin side; answer engines favour pages with "
                "600+ words of extractable substance."
            )
        else:
            score, status, rec = 0.3, Status.FAIL, (
                "Very thin content (<300 words). RAG pipelines have almost nothing to "
                "retrieve — expand the page's factual core."
            )
        return Finding(
            check_id="seo.word_count",
            title="Content volume",
            status=status,
            score=score,
            weight=6.0,
            details=f"{words} words of boilerplate-stripped main content.",
            recommendation=rec,
        )

    def _check_text_to_code(self, snap: PageSnapshot) -> Finding:
        ratio = snap.text_to_code_ratio
        if ratio >= 0.15:
            score, status, rec = 1.0, Status.PASS, ""
        elif ratio >= 0.07:
            score, status, rec = 0.6, Status.WARN, (
                "Markup outweighs visible text; strip boilerplate wrappers or add substance."
            )
        else:
            score, status, rec = 0.2, Status.FAIL, (
                "Text-to-code ratio below 7% — the DOM is mostly chrome/scripts, which "
                "degrades extraction quality in both indexers and LLM crawlers."
            )
        return Finding(
            check_id="seo.text_to_code",
            title="Text-to-code ratio",
            status=status,
            score=score,
            weight=6.0,
            details=f"Visible text is {ratio:.1%} of the raw HTML payload.",
            recommendation=rec,
        )

    def _check_security_headers(self, snap: PageSnapshot) -> Finding:
        if not snap.headers:
            return Finding(
                check_id="seo.security_headers",
                title="Security headers",
                status=Status.INFO,
                score=1.0,
                weight=0.0,
                details="Raw HTML input — response headers not available.",
                recommendation="",
            )
        present = []
        for header in SECURITY_HEADERS:
            value = snap.header(header)
            if header == "x-frame-options":
                csp = snap.header("content-security-policy") or ""
                if value or "frame-ancestors" in csp.lower():
                    present.append(header)
            elif value:
                present.append(header)
        score = len(present) / len(SECURITY_HEADERS)
        missing = [h for h in SECURITY_HEADERS if h not in present]
        status = Status.PASS if score >= 0.75 else (Status.WARN if score >= 0.5 else Status.FAIL)
        return Finding(
            check_id="seo.security_headers",
            title="Security headers",
            status=status,
            score=score,
            weight=6.0,
            details=(f"{len(present)}/{len(SECURITY_HEADERS)} present"
                     + (f"; missing: {', '.join(missing)}" if missing else "")),
            recommendation="" if score >= 0.75 else
            "Send HSTS, Content-Security-Policy, X-Content-Type-Options and "
            "X-Frame-Options (or CSP frame-ancestors) — hardening headers are a "
            "corroborating trust signal for search and agentic fetchers.",
        )

    def _check_cache_headers(self, snap: PageSnapshot) -> Finding:
        if not snap.headers:
            return Finding(
                check_id="seo.cache_headers",
                title="Cache/validation headers",
                status=Status.INFO,
                score=1.0,
                weight=0.0,
                details="Raw HTML input — response headers not available.",
                recommendation="",
            )
        present = [h for h in CACHE_HEADERS if snap.header(h)]
        score = 1.0 if present else 0.0
        return Finding(
            check_id="seo.cache_headers",
            title="Cache/validation headers",
            status=Status.PASS if present else Status.WARN,
            score=score,
            weight=3.0,
            details=(f"Found: {', '.join(present)}." if present else
                     "No Cache-Control/ETag/Last-Modified headers."),
            recommendation="" if present else
            "Emit Cache-Control plus ETag or Last-Modified so crawlers and AI agents "
            "can revalidate instead of re-downloading — a real crawl-budget signal.",
        )

    def _check_robots_ai_crawlers(self, snap: PageSnapshot) -> Finding:
        if snap.robots_txt is None:
            if snap.status_code == 0:
                return Finding(
                    check_id="seo.robots_ai_crawlers",
                    title="robots.txt AI-crawler policy",
                    status=Status.INFO,
                    score=1.0,
                    weight=0.0,
                    details="Raw HTML input — robots.txt not evaluated.",
                    recommendation="",
                )
            return Finding(
                check_id="seo.robots_ai_crawlers",
                title="robots.txt AI-crawler policy",
                status=Status.WARN,
                score=0.4,
                weight=4.0,
                details="robots.txt missing or unreachable; AI crawlers default to full access "
                "and you cannot express opt-outs/opt-ins.",
                recommendation="Publish /robots.txt with explicit rules for GPTBot, "
                "PerplexityBot, ClaudeBot, Google-Extended, Amazonbot and Applebot-Extended.",
            )
        verdicts = ai_crawler_verdicts(snap.robots_txt)
        blocked = [bot for bot, verdict in verdicts.items() if verdict == "blocked"]
        if not blocked:
            score, status, rec = 1.0, Status.PASS, ""
        elif len(blocked) <= 2:
            score, status, rec = 0.6, Status.WARN, (
                f"{len(blocked)} AI crawler(s) blocked ({', '.join(blocked)}): pages disallowed "
                "in robots.txt are invisible to those answer engines. Confirm this is intentional."
            )
        else:
            score, status, rec = 0.2, Status.FAIL, (
                f"{len(blocked)} AI crawlers blocked ({', '.join(blocked)}). The site is opting "
                "out of ChatGPT/Perplexity/Claude-style discovery — revisit unless deliberate."
            )
        return Finding(
            check_id="seo.robots_ai_crawlers",
            title="robots.txt AI-crawler policy",
            status=status,
            score=score,
            weight=10.0,
            details="; ".join(f"{bot}: {verdict}" for bot, verdict in verdicts.items()),
            recommendation=rec,
        )
