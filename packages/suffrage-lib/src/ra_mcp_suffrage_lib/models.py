"""Pydantic models for women's suffrage records."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


def _clean(value: str | None) -> str:
    """Convert None or whitespace-only to empty string, strip whitespace."""
    if value is None:
        return ""
    stripped = value.strip()
    return stripped


class RostrattRecord(BaseModel):
    """A signature record from the women's suffrage petition 1913-1914."""

    model_config = ConfigDict(populate_by_name=True)

    lan: str = ""
    ortens_namn: str = ""
    fornamn: str = ""
    efternamn: str = ""
    titel: str = ""
    yrke: str = ""
    adress: str = ""
    bidrag_kr: str = ""
    bidrag_ore: str = ""
    fodelseuppgift: str = ""
    ovriga_anteckningar: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> RostrattRecord:
        """Construct a RostrattRecord from a raw CSV row dict.

        The CSV uses semicolon delimiters, latin-1 encoding, and Swedish-char
        headers (e.g. Förnamn, Efternamn, Länets_namn).
        """
        return cls(
            lan=_clean(row.get("Länets_namn", row.get("Lanets_namn", ""))),
            ortens_namn=_clean(row.get("Ortens_namn", "")),
            fornamn=_clean(row.get("Förnamn", row.get("Fornamn", ""))),
            efternamn=_clean(row.get("Efternamn", "")),
            titel=_clean(row.get("Titel", "")),
            yrke=_clean(row.get("Yrke", "")),
            adress=_clean(row.get("Adress", "")),
            bidrag_kr=_clean(row.get("Bidrag_Kr", "")),
            bidrag_ore=_clean(row.get("Bidrag_öre", row.get("Bidrag_ore", ""))),
            fodelseuppgift=_clean(row.get("Födelseuppgift", row.get("Fodelseuppgift", ""))),
            ovriga_anteckningar=_clean(row.get("Övriga_anteckningar", row.get("Ovriga_anteckningar", ""))),
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.fornamn,
            self.efternamn,
            self.titel,
            self.yrke,
            self.adress,
            self.ortens_namn,
            self.lan,
            self.ovriga_anteckningar,
        ]
        return " ".join(p for p in parts if p)


class FKPRRecord(BaseModel):
    """A member record from the Gothenburg FKPR suffrage association 1911-1920."""

    model_config = ConfigDict(populate_by_name=True)

    efternamn: str = ""
    foernamn: str = ""
    titel_yrke: str = ""
    adress: str = ""
    anteckningar: str = ""
    membership_years: list[int] = []

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> FKPRRecord:
        """Construct a FKPRRecord from a raw CSV row dict.

        The CSV uses semicolon delimiters, latin-1 encoding. Year columns
        (1911-1920) contain "1" for membership that year.
        """
        years = []
        for year in range(1911, 1921):
            val = row.get(str(year), "").strip()
            if val == "1":
                years.append(year)

        return cls(
            efternamn=_clean(row.get("EFTERNAMN", "")),
            foernamn=_clean(row.get("FOERNAMN", "")),
            titel_yrke=_clean(row.get("TITEL_YRKE", "")),
            adress=_clean(row.get("ADRESS", "")),
            anteckningar=_clean(row.get("ANTECKNINGAR", "")),
            membership_years=years,
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.efternamn,
            self.foernamn,
            self.titel_yrke,
            self.adress,
            self.anteckningar,
        ]
        return " ".join(p for p in parts if p)
