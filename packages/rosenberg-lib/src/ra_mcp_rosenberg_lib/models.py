"""Pydantic models for Rosenberg's geographical lexicon records."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


# Mapping from Swedish-character CSV headers to ASCII field names
_INDUSTRY_CSV_MAP: dict[str, str] = {
    "kalkbränning": "kalkbranning",
    "tändstikor": "tandstikor",
    "fyr": "fyr",
    "färjställe": "farjstalle",
    "fisk": "fisk",
    "bränneri": "branneri",
    "stambana": "stambana",
    "jernverk": "jernverk",
    "tegelbruk": "tegelbruk",
    "mjölsfabrik": "mjolsfabrik",
    "gjuteri": "gjuteri",
    "gästgifveri": "gastgifveri",
    "säteri": "sateri",
    "jernväg": "jernvag",
    "grufva": "grufva",
    "såg": "sag",
    "qvarn": "qvarn",
}

# Human-readable Swedish names for each industry flag
_INDUSTRY_DISPLAY: dict[str, str] = {
    "kalkbranning": "Kalkbränning",
    "tandstikor": "Tändstikor",
    "fyr": "Fyr",
    "farjstalle": "Färjställe",
    "fisk": "Fisk",
    "branneri": "Bränneri",
    "stambana": "Stambana",
    "jernverk": "Jernverk",
    "tegelbruk": "Tegelbruk",
    "mjolsfabrik": "Mjölsfabrik",
    "gjuteri": "Gjuteri",
    "gastgifveri": "Gästgifveri",
    "sateri": "Säteri",
    "jernvag": "Jernväg",
    "grufva": "Grufva",
    "sag": "Såg",
    "qvarn": "Qvarn",
}


def _clean(value: str | None) -> str:
    """Convert None or whitespace-only to empty string, strip whitespace."""
    if value is None:
        return ""
    stripped = value.strip()
    return stripped


class RosenbergRecord(BaseModel):
    """A record from Rosenberg's geographical lexicon of Sweden."""

    model_config = ConfigDict(populate_by_name=True)

    post_id: int
    url: str = ""
    plats: str = ""
    forsamling: str = ""
    harad: str = ""
    tingslag: str = ""
    lan: str = ""
    beskrivning: str = ""

    # Boolean industry flags (empty or "1")
    kalkbranning: str = ""
    tandstikor: str = ""
    fyr: str = ""
    farjstalle: str = ""
    fisk: str = ""
    branneri: str = ""
    stambana: str = ""
    jernverk: str = ""
    tegelbruk: str = ""
    mjolsfabrik: str = ""
    gjuteri: str = ""
    gastgifveri: str = ""
    sateri: str = ""
    jernvag: str = ""
    grufva: str = ""
    sag: str = ""
    qvarn: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> RosenbergRecord:
        """Construct a RosenbergRecord from a raw CSV row dict.

        The CSV uses semicolon delimiters, latin-1 encoding.
        Swedish-character column headers are mapped to ASCII field names.
        """
        industry_values = {}
        for csv_header, field_name in _INDUSTRY_CSV_MAP.items():
            industry_values[field_name] = _clean(row.get(csv_header, ""))

        return cls(
            post_id=int(row["PostID"]),
            url=_clean(row.get("URL", "")),
            plats=_clean(row.get("Plats", "")),
            forsamling=_clean(row.get("Forsamling", "")),
            harad=_clean(row.get("Harad", "")),
            tingslag=_clean(row.get("Tingslag", "")),
            lan=_clean(row.get("Lan", "")),
            beskrivning=_clean(row.get("Beskrivning", "")),
            **industry_values,
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.plats,
            self.forsamling,
            self.harad,
            self.tingslag,
            self.lan,
            self.beskrivning,
        ]
        return " ".join(p for p in parts if p)

    @property
    def industries(self) -> list[str]:
        """Return human-readable names of industries flagged with '1'."""
        result = []
        for field_name, display_name in _INDUSTRY_DISPLAY.items():
            if getattr(self, field_name) == "1":
                result.append(display_name)
        return result
