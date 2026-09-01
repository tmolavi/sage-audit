"""FastMCP server — SAGE audits as autonomous tools for AI agents.

Exposes four tools over the Model Context Protocol:

    sage_audit_url(url)          → full 3-pillar audit of a live page
    sage_audit_html(html, url)   → offline audit of raw HTML
    sage_generate_llms_txt(url)  → optimized llms.txt manifest
    sage_version()               → package metadata

Compatible with both generations of the official MCP SDK:
  * mcp 1.x  →  mcp.server.fastmcp.FastMCP
  * mcp 2.x  →  mcp.server.mcpserver.MCPServer (FastMCP renamed)

Register in Claude Desktop (`claude_desktop_config.json`)::

    {
      "mcpServers": {
        "sage-audit": {
          "command": "sage",
          "args": ["mcp"]
        }
      }
    }

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from sage_audit._version import __version__
from sage_audit.core import SageAuditor
from sage_audit.utils.extractor import FetchError

logger = logging.getLogger("sage_audit.mcp")

_ServerClass: Any = None
_API: Optional[str] = None
_IMPORT_ERROR: Optional[str] = None

try:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _ServerClass  # type: ignore

    _API = "v1"
except Exception as exc_v1:  # pragma: no cover - depends on installed SDK
    _IMPORT_ERROR = f"{type(exc_v1).__name__}: {exc_v1}"
    try:  # mcp 2.x (FastMCP renamed to MCPServer)
        from mcp.server.mcpserver import MCPServer as _ServerClass  # type: ignore

        _API = "v2"
        _IMPORT_ERROR = None
    except Exception as exc_v2:  # pragma: no cover - depends on installed SDK
        _IMPORT_ERROR = f"{type(exc_v2).__name__}: {exc_v2}"

INSTRUCTIONS = (
    "SAGE (Search, Answer, & Generative Engine Auditor) evaluates any URL or "
    "raw HTML across three pillars — Technical SEO, Answer Engine "
    "Optimization (AEO: JSON-LD entity graphs, direct-answer density, sameAs "
    "authority) and Generative Engine Optimization (GEO: semantic chunking, "
    "RAG retrieval simulation, Citation Survival Probability) — and returns a "
    "weighted 0-100 verdict with prioritized fixes plus generated llms.txt "
    "and rag_ready_chunks.json artifacts."
)

INSTALL_HINT = (
    "The 'mcp' package is not installed (or unusable). Install it with "
    "`pip install sage-audit[mcp]` or `pip install 'mcp>=1.2'`."
)


class SageMCPServer:
    """Thin adapter normalizing mcp 1.x / 2.x differences.

    Delegates attribute access to the wrapped SDK server, and translates
    ``run()`` kwargs (v1 takes host/port on the constructor, v2 on ``run``).
    """

    def __init__(self, server: Any, api: str, host: str, port: int) -> None:
        self._server = server
        self._api = api
        self._host = host
        self._port = port

    def __getattr__(self, item: str) -> Any:
        return getattr(self._server, item)

    def run(self, transport: str = "stdio") -> None:
        kwargs: dict[str, Any] = {"transport": transport}
        if self._api == "v2" and transport != "stdio":
            kwargs.update({"host": self._host, "port": self._port})
        self._server.run(**kwargs)


def create_server(host: str = "127.0.0.1", port: int = 8642) -> SageMCPServer:
    """Build the configured MCP server with all SAGE tools registered."""

    if _ServerClass is None or _API is None:
        raise RuntimeError(INSTALL_HINT + (f" ({_IMPORT_ERROR})" if _IMPORT_ERROR else ""))

    kwargs: dict[str, Any] = {
        "name": "sage-audit",
        "instructions": INSTRUCTIONS,
    }
    if _API == "v1":
        kwargs["host"] = host
        kwargs["port"] = port
    else:  # v2
        kwargs["version"] = __version__
    try:
        server = _ServerClass(**kwargs)
    except TypeError:  # very defensive: SDK signature drift
        server = _ServerClass(name="sage-audit")

    @server.tool()
    def sage_audit_url(url: str, embedding_backend: str = "auto") -> dict[str, Any]:
        """Run the full SAGE 3-pillar audit (SEO + AEO + GEO) against a live URL.

        Returns the complete report: pillar scores, letter grades, every
        finding with evidence and fixes, GEO retrieval simulation metrics,
        and generated artifacts (llms.txt, rag_ready_chunks.json).
        """

        try:
            report = SageAuditor(embedding_backend=embedding_backend).audit(url)
        except FetchError as exc:
            return {"error": str(exc), "url": url}
        except Exception as exc:  # never kill the agent loop
            return {"error": f"{type(exc).__name__}: {exc}", "url": url}
        return report.to_dict()

    @server.tool()
    def sage_audit_html(
        html: str, url: str = "https://example.local/"
    ) -> dict[str, Any]:
        """Audit raw HTML offline (no network): same 3-pillar report as
        sage_audit_url, minus transport checks (headers/robots.txt)."""

        try:
            report = SageAuditor().audit_html(html, url=url)
        except Exception as exc:
            return {"error": f"{type(exc).__name__}: {exc}"}
        return report.to_dict()

    @server.tool()
    def sage_generate_llms_txt(url: str) -> str:
        """Generate an optimized llms.txt manifest (llmstxt.org) for a URL."""

        try:
            return SageAuditor().generate_llms_txt(url)
        except FetchError as exc:
            return f"ERROR: {exc}"
        except Exception as exc:
            return f"ERROR: {type(exc).__name__}: {exc}"

    @server.tool()
    def sage_version() -> dict[str, str]:
        """Return sage-audit version and authorship metadata."""

        return {
            "name": "sage-audit",
            "version": __version__,
            "tagline": "The Unified 3-Pillar Audit Engine for SEO, Entity AEO, and GEO.",
            "author": "Taqi Molavi",
            "website": "https://molavi.pro",
            "research": "https://molavi.pro/research",
            "license": "MIT",
        }

    return SageMCPServer(server=server, api=_API, host=host, port=port)


def run_server(transport: str = "stdio", host: str = "0.0.0.0", port: int = 8642) -> None:
    """Create and run the MCP server (blocking)."""

    create_server(host=host, port=port).run(transport=transport)


if __name__ == "__main__":  # pragma: no cover
    run_server()
