"""Pydantic models for Swedish church records (births, deaths, marriages)."""

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


class FodelseRecord(BaseModel):
    """A birth record from Swedish church books (församlingsböcker)."""

    model_config = ConfigDict(populate_by_name=True)

    postid: str = ""
    forsamling: str = ""
    lan: str = ""
    datum: str = ""
    fornamn: str = ""
    kon: str = ""
    far_fornamn: str = ""
    far_efternamn: str = ""
    far_yrke: str = ""
    far_ort: str = ""
    mor_fornamn: str = ""
    mor_efternamn: str = ""
    mor_yrke: str = ""
    fodelseort: str = ""
    dopvittne: str = ""
    anm: str = ""
    referenskod: str = ""
    volym: str = ""
    bild_id: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> FodelseRecord:
        """Construct a FodelseRecord from a raw CSV row dict.

        The CSV uses semicolon delimiters, latin-1 encoding, and NULL as sentinel.
        """
        return cls(
            postid=_clean(row.get("Postid", "")),
            forsamling=_clean(row.get("Forsamling", "")),
            lan=_clean(row.get("Lan", "")),
            datum=_clean(row.get("Datum", "")),
            fornamn=_clean(row.get("Fornamn", "")),
            kon=_clean(row.get("Kon", "")),
            far_fornamn=_clean(row.get("Far_fornamn", "")),
            far_efternamn=_clean(row.get("Far_efternamn", "")),
            far_yrke=_clean(row.get("Far_yrke", "")),
            far_ort=_clean(row.get("Far_ort", "")),
            mor_fornamn=_clean(row.get("Mor_fornamn", "")),
            mor_efternamn=_clean(row.get("Mor_efternamn", "")),
            mor_yrke=_clean(row.get("Mor_yrke", "")),
            fodelseort=_clean(row.get("Fodelseort", "")),
            dopvittne=_clean(row.get("Dopvittne", "")),
            anm=_clean(row.get("Anm", "")),
            referenskod=_clean(row.get("Referenskod", "")),
            volym=_clean(row.get("Volym", "")),
            bild_id=_clean(row.get("BildID", "")),
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.fornamn,
            self.far_fornamn,
            self.far_efternamn,
            self.far_yrke,
            self.mor_fornamn,
            self.mor_efternamn,
            self.fodelseort,
            self.forsamling,
            self.lan,
            self.anm,
        ]
        return " ".join(p for p in parts if p)


class DodaRecord(BaseModel):
    """A death record from Swedish church books (församlingsböcker)."""

    model_config = ConfigDict(populate_by_name=True)

    postid: str = ""
    forsamling: str = ""
    lan: str = ""
    datum: str = ""
    fornamn: str = ""
    efternamn: str = ""
    yrke: str = ""
    hemort: str = ""
    kon: str = ""
    civilstand: str = ""
    alder: str = ""
    dodsorsak: str = ""
    dodsorsak_klassificerat: str = ""
    anhorig_fornamn: str = ""
    anhorig_efternamn: str = ""
    anhorig_yrke: str = ""
    anhorig_relation: str = ""
    anm: str = ""
    referenskod: str = ""
    volym: str = ""
    bild_id: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> DodaRecord:
        """Construct a DodaRecord from a raw CSV row dict.

        The CSV uses semicolon delimiters, latin-1 encoding, and NULL as sentinel.
        """
        return cls(
            postid=_clean(row.get("PostID", "")),
            forsamling=_clean(row.get("Forsamling", "")),
            lan=_clean(row.get("Lan", "")),
            datum=_clean(row.get("Datum", "")),
            fornamn=_clean(row.get("Fornamn", "")),
            efternamn=_clean(row.get("Efternamn", "")),
            yrke=_clean(row.get("Yrke", "")),
            hemort=_clean(row.get("Hemort", "")),
            kon=_clean(row.get("Kon", "")),
            civilstand=_clean(row.get("Civilstand", "")),
            alder=_clean(row.get("Alder", "")),
            dodsorsak=_clean(row.get("Dodsorsak", "")),
            dodsorsak_klassificerat=_clean(row.get("Dodsorsak_klassificerat", "")),
            anhorig_fornamn=_clean(row.get("Anhorig_fornamn", "")),
            anhorig_efternamn=_clean(row.get("Anhorig_efternamn", "")),
            anhorig_yrke=_clean(row.get("Anhorig_yrke", "")),
            anhorig_relation=_clean(row.get("Anhorig_relation", "")),
            anm=_clean(row.get("Anm", "")),
            referenskod=_clean(row.get("Referenskod", "")),
            volym=_clean(row.get("Volym", "")),
            bild_id=_clean(row.get("BildID", "")),
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.fornamn,
            self.efternamn,
            self.yrke,
            self.hemort,
            self.dodsorsak,
            self.dodsorsak_klassificerat,
            self.anhorig_fornamn,
            self.anhorig_efternamn,
            self.forsamling,
            self.lan,
            self.anm,
        ]
        return " ".join(p for p in parts if p)


class VigselRecord(BaseModel):
    """A marriage record from Swedish church books (församlingsböcker)."""

    model_config = ConfigDict(populate_by_name=True)

    postid: str = ""
    forsamling: str = ""
    lan: str = ""
    datum: str = ""
    brudgum_fornamn: str = ""
    brudgum_efternamn: str = ""
    brudgum_yrke: str = ""
    brudgum_hemort: str = ""
    brudgum_civilstand: str = ""
    brudgum_alder: str = ""
    brud_fornamn: str = ""
    brud_efternamn: str = ""
    brud_yrke: str = ""
    brud_hemort: str = ""
    brud_alder: str = ""
    anm: str = ""
    referenskod: str = ""
    volym: str = ""
    bild_id: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> VigselRecord:
        """Construct a VigselRecord from a raw CSV row dict.

        The CSV uses semicolon delimiters, latin-1 encoding, and NULL as sentinel.
        Note: CSV has Brud_Alder (capital A), mapped to brud_alder.
        """
        return cls(
            postid=_clean(row.get("Postid", "")),
            forsamling=_clean(row.get("Forsamling", "")),
            lan=_clean(row.get("Lan", "")),
            datum=_clean(row.get("Datum", "")),
            brudgum_fornamn=_clean(row.get("Brudgum_fornamn", "")),
            brudgum_efternamn=_clean(row.get("Brudgum_efternamn", "")),
            brudgum_yrke=_clean(row.get("Brudgum_yrke", "")),
            brudgum_hemort=_clean(row.get("Brudgum_hemort", "")),
            brudgum_civilstand=_clean(row.get("Brudgum_civilstand", "")),
            brudgum_alder=_clean(row.get("Brudgum_alder", "")),
            brud_fornamn=_clean(row.get("Brud_fornamn", "")),
            brud_efternamn=_clean(row.get("Brud_efternamn", "")),
            brud_yrke=_clean(row.get("Brud_yrke", "")),
            brud_hemort=_clean(row.get("Brud_hemort", "")),
            brud_alder=_clean(row.get("Brud_Alder", "")),
            anm=_clean(row.get("Anm", "")),
            referenskod=_clean(row.get("Referenskod", "")),
            volym=_clean(row.get("Volym", "")),
            bild_id=_clean(row.get("BildID", "")),
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.brudgum_fornamn,
            self.brudgum_efternamn,
            self.brudgum_yrke,
            self.brudgum_hemort,
            self.brud_fornamn,
            self.brud_efternamn,
            self.brud_yrke,
            self.brud_hemort,
            self.forsamling,
            self.lan,
            self.anm,
        ]
        return " ".join(p for p in parts if p)
