"""Pydantic models for Filmcensur (Swedish film censorship) records."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


def _clean(value: str | None) -> str:
    """Convert NULL sentinel, '-', or None to empty string, strip whitespace."""
    if value is None:
        return ""
    stripped = value.strip()
    if stripped in ("", "-"):
        return ""
    return stripped


class FilmregRecord(BaseModel):
    """A record from the Swedish film censorship registry (Filmregistret)."""

    model_config = ConfigDict(populate_by_name=True)

    granskningsnummer: int
    titel_org: str = ""
    titel_svensk: str = ""
    titel_annan: str = ""
    produktionsaar: str = ""
    filmkategori: str = ""
    filmtyp: str = ""
    produktionsland: str = ""
    fri_text: str = ""
    beslutsdatum: str = ""
    aaldersgraens: str = ""
    klipp_antal: str = ""
    producent: str = ""
    beslut_laengd: str = ""
    noteringar: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> FilmregRecord:
        """Construct a FilmregRecord from a raw CSV row dict.

        The CSV uses semicolon delimiters, latin-1 encoding, and the string
        ``-`` as a sentinel for missing values.
        """
        return cls(
            granskningsnummer=int(row["Granskningsnummer"]),
            titel_org=_clean(row.get("Titel_Org", "")),
            titel_svensk=_clean(row.get("Titel_Svensk", "")),
            titel_annan=_clean(row.get("Titel_Annan", "")),
            produktionsaar=_clean(row.get("Produktionsaar", "")),
            filmkategori=_clean(row.get("Filmkategori", "")),
            filmtyp=_clean(row.get("Filmtyp", "")),
            produktionsland=_clean(row.get("Produktionsland", "")),
            fri_text=_clean(row.get("Fri_Text", "")),
            beslutsdatum=_clean(row.get("Beslutsdatum", "")),
            aaldersgraens=_clean(row.get("AAldersgraens", "")),
            klipp_antal=_clean(row.get("Klipp_Antal", "")),
            producent=_clean(row.get("Producent", "")),
            beslut_laengd=_clean(row.get("Beslut_laengd_foere_tid", "")),
            noteringar=_clean(row.get("Noteringar", "")),
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.titel_org,
            self.titel_svensk,
            self.titel_annan,
            self.produktionsland,
            self.filmkategori,
            self.fri_text,
            self.producent,
            self.noteringar,
            self.aaldersgraens,
        ]
        return " ".join(p for p in parts if p)
