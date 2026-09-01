"""Tokenization, sentence splitting, and lightweight vector math utilities.

These helpers are shared by the AEO pillar (direct-answer analysis) and the
GEO pillar (semantic chunking, retrieval simulation). They intentionally use
only the standard library so the fallback embedding pipeline is fully
deterministic and portable.

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

import math
import re
from typing import Sequence

# Approximate LLM token segmentation: words or individual punctuation marks.
# Works for Latin, Persian (Farsi), Arabic and Turkish scripts because \w is
# Unicode-aware in Python 3.
TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)
WORD_RE = re.compile(r"\w+", re.UNICODE)
LOWER_TOKEN_RE = re.compile(r"[a-z0-9\u00c0-\u017e\u0600-\u06ff]+", re.UNICODE)

# Sentence boundaries: ., !, ?, Persian question mark, ellipsis, or newlines.
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?؟…])\s+|\n+")


def count_tokens(text: str) -> int:
    """Approximate the number of LLM tokens in ``text``."""

    if not text:
        return 0
    return len(TOKEN_RE.findall(text))


def count_words(text: str) -> int:
    """Count whitespace-delimited words."""

    if not text:
        return 0
    return len(text.split())


def split_sentences(text: str) -> list[str]:
    """Split text into sentences (supports Latin + Persian punctuation)."""

    if not text:
        return []
    return [part.strip() for part in SENTENCE_SPLIT_RE.split(text) if part and part.strip()]


def truncate(text: str, limit: int = 120) -> str:
    """Truncate ``text`` on a word boundary, appending an ellipsis if needed."""

    text = (text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(" .,;:") + "…"


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Pure-Python cosine similarity between two equal-length vectors."""

    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    if norm_a <= 0.0 or norm_b <= 0.0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


def normalized_softmax_entropy(similarities: Sequence[float], temperature: float = 1.0) -> float:
    """Entropy of the softmax over ``similarities``, normalized to [0, 1].

    0.0  -> retrieval attention is fully concentrated on one chunk (ideal).
    1.0  -> attention is uniform across chunks (maximum ambiguity).
    """

    n = len(similarities)
    if n <= 1:
        return 0.0
    temp = max(temperature, 1e-6)
    peak = max(similarities)
    exps = [math.exp((s - peak) / temp) for s in similarities]
    total = sum(exps)
    if total <= 0.0:
        return 0.0
    entropy = 0.0
    for value in exps:
        p = value / total
        if p > 0.0:
            entropy -= p * math.log(p)
    return entropy / math.log(n)


def mean(values: Sequence[float]) -> float:
    """Safe arithmetic mean (0.0 for empty input)."""

    return sum(values) / len(values) if values else 0.0


def stddev(values: Sequence[float]) -> float:
    """Population standard deviation."""

    if not values:
        return 0.0
    mu = mean(values)
    return math.sqrt(sum((v - mu) ** 2 for v in values) / len(values))
