"""Pydantic models for Sjömanshus (seaman house) records."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


def _clean(value: str | None) -> str:
    """Convert NULL sentinel or None to empty string, strip whitespace."""
    if value is None:
        return ""
    stripped = value.strip()
    if stripped == "NULL":
        return ""
    return stripped


class LiggareRecord(BaseModel):
    """A voyage/employment record from a Sjömanshus liggare."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    foernamn: str = ""
    efternamn1: str = ""
    efternamn2: str = ""
    foedelsedat: str = ""
    aalder: str = ""
    foedelseplats: str = ""
    foedelsefoers: str = ""
    hemplats: str = ""
    hemfoers: str = ""
    civilstaand: str = ""
    sjoemanshus: str = ""
    inskrivnr: str = ""
    befattning_yrke: str = ""
    paamoenstort: str = ""
    paamoenstdat: str = ""
    avmoenstort: str = ""
    avmoenstdat: str = ""
    orsak: str = ""
    anm: str = ""
    fartyg: str = ""
    typ: str = ""
    hemmahamn: str = ""
    destination: str = ""
    redare: str = ""
    kapten: str = ""
    oevrigt: str = ""
    volym: str = ""
    sida: str = ""
    arkiv: str = ""
    arkivnr: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> LiggareRecord:
        """Construct a LiggareRecord from a raw CSV row dict.

        The CSV uses semicolon delimiters, latin-1 encoding, and empty strings
        for missing values.
        """
        return cls(
            id=int(row["ID"]),
            foernamn=_clean(row.get("Foernamn", "")),
            efternamn1=_clean(row.get("Efternamn1", "")),
            efternamn2=_clean(row.get("Efternamn2", "")),
            foedelsedat=_clean(row.get("Foedelsedat", "")),
            aalder=_clean(row.get("Aalder", "")),
            foedelseplats=_clean(row.get("Foedelseplats", "")),
            foedelsefoers=_clean(row.get("Foedelsefoers", "")),
            hemplats=_clean(row.get("Hemplats", "")),
            hemfoers=_clean(row.get("Hemfoers", "")),
            civilstaand=_clean(row.get("Civilstaand", "")),
            sjoemanshus=_clean(row.get("Sjoemanshus", "")),
            inskrivnr=_clean(row.get("Inskrivnr", "")),
            befattning_yrke=_clean(row.get("Befattning_Yrke", "")),
            paamoenstort=_clean(row.get("Paamoenstort", "")),
            paamoenstdat=_clean(row.get("Paamoenstdat", "")),
            avmoenstort=_clean(row.get("Avmoenstort", "")),
            avmoenstdat=_clean(row.get("Avmoenstdat", "")),
            orsak=_clean(row.get("Orsak", "")),
            anm=_clean(row.get("Anm", "")),
            fartyg=_clean(row.get("Fartyg", "")),
            typ=_clean(row.get("Typ", "")),
            hemmahamn=_clean(row.get("Hemmahamn", "")),
            destination=_clean(row.get("Destination", "")),
            redare=_clean(row.get("Redare", "")),
            kapten=_clean(row.get("Kapten", "")),
            oevrigt=_clean(row.get("Oevrigt", "")),
            volym=_clean(row.get("Volym", "")),
            sida=_clean(row.get("Sida", "")),
            arkiv=_clean(row.get("Arkiv", "")),
            arkivnr=_clean(row.get("Arkisnr", "")),
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.foernamn,
            self.efternamn1,
            self.efternamn2,
            self.befattning_yrke,
            self.fartyg,
            self.hemmahamn,
            self.destination,
            self.redare,
            self.kapten,
            self.foedelsefoers,
            self.hemfoers,
            self.oevrigt,
        ]
        return " ".join(p for p in parts if p)


class MatrikelRecord(BaseModel):
    """A seaman registration record from a Sjömanshus matrikel."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    foernamn: str = ""
    efternamn1: str = ""
    efternamn2: str = ""
    foedelsedat: str = ""
    foedelseplats: str = ""
    foedelsefoers: str = ""
    hemplats: str = ""
    hemfoers: str = ""
    far: str = ""
    mor: str = ""
    sjoemanshus: str = ""
    inskrivnr: str = ""
    inskrivdat: str = ""
    avfoerdort: str = ""
    avfoerddat: str = ""
    orsak: str = ""
    anm: str = ""
    oevrigt: str = ""
    volym: str = ""
    sida: str = ""
    arkiv: str = ""
    arkivnr: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> MatrikelRecord:
        """Construct a MatrikelRecord from a raw CSV row dict.

        The CSV uses semicolon delimiters, latin-1 encoding, and empty strings
        for missing values.
        """
        return cls(
            id=int(row["ID"]),
            foernamn=_clean(row.get("Foernamn", "")),
            efternamn1=_clean(row.get("Efternamn1", "")),
            efternamn2=_clean(row.get("Efternamn2", "")),
            foedelsedat=_clean(row.get("Foedelsedat", "")),
            foedelseplats=_clean(row.get("Foedelseplats", "")),
            foedelsefoers=_clean(row.get("Foedelsefoers", "")),
            hemplats=_clean(row.get("Hemplats", "")),
            hemfoers=_clean(row.get("Hemfoers", "")),
            far=_clean(row.get("Far", "")),
            mor=_clean(row.get("Mor", "")),
            sjoemanshus=_clean(row.get("Sjoemanshus", "")),
            inskrivnr=_clean(row.get("Inskrivnr", "")),
            inskrivdat=_clean(row.get("Inskrivdat", "")),
            avfoerdort=_clean(row.get("Avfoerdort", "")),
            avfoerddat=_clean(row.get("Avfoerddat", "")),
            orsak=_clean(row.get("Orsak", "")),
            anm=_clean(row.get("Anm", "")),
            oevrigt=_clean(row.get("Oevrigt", "")),
            volym=_clean(row.get("Volym", "")),
            sida=_clean(row.get("Sida", "")),
            arkiv=_clean(row.get("Arkiv", "")),
            arkivnr=_clean(row.get("Arkisnr", "")),
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.foernamn,
            self.efternamn1,
            self.efternamn2,
            self.far,
            self.mor,
            self.foedelsefoers,
            self.hemfoers,
            self.oevrigt,
        ]
        return " ".join(p for p in parts if p)
