"""Configuration management for sage-audit heuristic thresholds and pipeline settings.

(c) 2026 Taqi Molavi — https://molavi.pro — MIT License
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class SageConfig(BaseModel):
    """Central configuration for SAGE 3-pillar audit rules and heuristic thresholds."""

    # ------------------------------------------------------------------ #
    # Transport & RAG Engine Settings
    # ------------------------------------------------------------------ #
    timeout: float = Field(default=20.0, description="Per-request network timeout (seconds).")
    fetch_robots: bool = Field(default=True, description="Whether to fetch and parse /robots.txt.")
    embedding_backend: str = Field(default="auto", description="Embedding backend ('auto', 'fastembed', 'sentence-transformers', 'hashing').")
    top_k: int = Field(default=3, description="Simulated RAG top-k retrieval depth.")
    max_sim_queries: int = Field(default=8, description="Maximum number of probe queries to simulate.")

    # ------------------------------------------------------------------ #
    # Pillar Score Weights (Sum = 1.0)
    # ------------------------------------------------------------------ #
    weight_seo: float = Field(default=0.30, description="Weight of Pillar 1 (Technical SEO).")
    weight_aeo: float = Field(default=0.35, description="Weight of Pillar 2 (Answer Engine Optimization).")
    weight_geo: float = Field(default=0.35, description="Weight of Pillar 3 (Generative Engine Optimization).")

    # ------------------------------------------------------------------ #
    # Pillar 1 — SEO Heuristic Thresholds (E4 / Configurable)
    # ------------------------------------------------------------------ #
    title_min_chars: int = Field(default=30, description="Ideal minimum title length in characters.")
    title_max_chars: int = Field(default=60, description="Ideal maximum title length in characters.")
    meta_desc_min_chars: int = Field(default=70, description="Ideal minimum meta description length in characters.")
    meta_desc_max_chars: int = Field(default=160, description="Ideal maximum meta description length in characters.")
    word_count_target: int = Field(default=600, description="Target word count for substantive body content.")
    word_count_min: int = Field(default=300, description="Minimum acceptable word count before severe penalty.")
    text_to_code_target_ratio: float = Field(default=0.15, description="Target visible text to HTML code ratio.")
    text_to_code_min_ratio: float = Field(default=0.07, description="Minimum acceptable text to code ratio.")
    image_alt_target_coverage: float = Field(default=0.90, description="Target percentage of images with alt attributes.")

    # ------------------------------------------------------------------ #
    # Pillar 2 — AEO Heuristic Thresholds (E4 / Configurable)
    # ------------------------------------------------------------------ #
    direct_answer_word_window: int = Field(default=70, description="Word window at section start evaluated for direct answer quality.")
    direct_answer_min_words: int = Field(default=8, description="Minimum words in a section for answer evaluation.")
    direct_answer_target_density: float = Field(default=0.55, description="Target average direct answer quality score across sections.")
    direct_answer_min_density: float = Field(default=0.35, description="Minimum acceptable direct answer score.")
    authority_sameas_target_count: int = Field(default=3, description="Target count of recognized authority sameAs profile links.")

    # ------------------------------------------------------------------ #
    # Pillar 3 — GEO & CSP Heuristics (E4 / E5 / Configurable)
    # ------------------------------------------------------------------ #
    chunk_min_tokens: int = Field(default=60, description="Lower token boundary for semantic passage chunking.")
    chunk_max_tokens: int = Field(default=120, description="Upper token boundary for semantic passage chunking.")
    chunk_overlap: int = Field(default=25, description="Token overlap carried between adjacent passage chunks.")
    content_volume_tokens_target: int = Field(default=600, description="Target approximate tokens for passage chunking.")
    content_volume_tokens_min: int = Field(default=240, description="Minimum approximate tokens required to form coherent chunks.")
    csp_prominence_weight: float = Field(default=0.6, description="Weight of retrieval prominence in CSP calculation.")
    csp_entropy_weight: float = Field(default=0.4, description="Weight of semantic entropy inverse in CSP calculation.")
    csp_pass_threshold: float = Field(default=70.0, description="CSP score threshold for pass status.")
    csp_warn_threshold: float = Field(default=45.0, description="CSP score threshold for warn status.")

    def update_from_dict(self, overrides: dict[str, Any]) -> SageConfig:
        """Return a new SageConfig updated with specified overrides."""
        current = self.model_dump()
        for k, v in overrides.items():
            if k in current and v is not None:
                current[k] = v
        return SageConfig(**current)
