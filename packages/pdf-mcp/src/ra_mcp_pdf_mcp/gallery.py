"""Curated gallery of available PDFs for the initial viewer."""

from __future__ import annotations


GALLERY_ITEMS: list[dict[str, str]] = [
    {
        "url": "https://filer.riksarkivet.se/nedladdningsbara-filer/Hur%20riket%20styrdes_63MB.pdf",
        "title": "Hur riket styrdes",
        "description": "Forvaltning, politik och arkiv 1520-1920 av Bjorn Asker (255 sidor)",
        "category": "Riksarkivet",
    },
    {
        "url": "https://arxiv.org/pdf/1706.03762",
        "title": "Attention Is All You Need",
        "description": "Vaswani et al. (2017) — The Transformer architecture paper",
        "category": "Academic",
    },
    {
        "url": "https://arxiv.org/pdf/2005.14165",
        "title": "GPT-3: Language Models are Few-Shot Learners",
        "description": "Brown et al. (2020) — 175B parameter language model",
        "category": "Academic",
    },
]


def get_gallery_items() -> list[dict[str, str]]:
    """Return the curated gallery items."""
    return GALLERY_ITEMS
