"""Curated gallery of available PDFs for the initial viewer."""

from __future__ import annotations


_HF_BASE = "https://huggingface.co/buckets/Riksarkivet/pdfs/resolve"

GALLERY_ITEMS: list[dict[str, str]] = [
    {
        "url": f"{_HF_BASE}/Hur%20riket%20styrdes_63MB.pdf?download=true",
        "title": "Hur riket styrdes",
        "description": "Forvaltning, politik och arkiv 1520-1920. Statsapparatens strukturer, grundlagar, kungen, riksdagen. Av Bjorn Asker (255 sidor)",
        "thumbnail_url": f"{_HF_BASE}/Hur%20riket%20styrdes_63MB.png?download=true",
        "category": "Riksarkivet",
    },
    {
        "url": f"{_HF_BASE}/216090389-e30a88-medeltidens-samhalle.pdf?download=true",
        "title": "Medeltidens samhalle",
        "description": "Arkivguide om medeltida Sverige: diplom, kungamakt, bonder, kyrkan, staderna. Baserad pa Riksarkivets medeltidssamlingar",
        "thumbnail_url": f"{_HF_BASE}/216090389-e30a88-medeltidens-samhalle.png?download=true",
        "category": "Riksarkivet",
    },
    {
        "url": f"{_HF_BASE}/164624875-f258a1-Ingang-till-samisk-historia_2024.pdf?download=true",
        "title": "Ingang till samisk historia",
        "description": "Guide till samisk historia i Riksarkivets samlingar (2024). Kallmaterial om samer i svenska arkiv",
        "thumbnail_url": f"{_HF_BASE}/164624875-f258a1-Ingang-till-samisk-historia_2024.png?download=true",
        "category": "Riksarkivet",
    },
]


def get_gallery_items() -> list[dict[str, str]]:
    """Return the curated gallery items."""
    return GALLERY_ITEMS
