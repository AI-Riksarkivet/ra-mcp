"""Pydantic models for SJ railway records (JUDA properties and FIRA/SIRA drawings)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


NULL_SENTINEL = "NULL"

# Column names for SIRA headerless CSV (same structure as FIRA)
RITNING_FIELDNAMES = [
    "BNUM",
    "BLAD",
    "AVD2",
    "UAVD",
    "RTYP2",
    "FORM2",
    "BDEL",
    "DATM",
    "RITN",
    "BEN1",
    "BEN",
    "SAKG",
    "SATS",
    "DKOD",
    "FILM",
    "AENDR",
    "FOERV",
    "UTLAA",
]


def _clean(value: str | None) -> str:
    """Convert None/NULL sentinel to empty string, strip whitespace."""
    if value is None:
        return ""
    stripped = value.strip().strip('"')
    if stripped == NULL_SENTINEL:
        return ""
    return stripped


class JudaRecord(BaseModel):
    """A property record from the SJ railway property register (JUDA)."""

    model_config = ConfigDict(populate_by_name=True)

    fbptyp: str = ""
    fbidnr: str = ""
    fbgvnr: str = ""
    fbtext: str = ""
    fblan: str = ""
    fbkom: str = ""
    fbfdbet: str = ""
    fbfdrgo: str = ""
    fbanm: str = ""
    fbagrkod2: str = ""
    fbbort: str = ""
    fbupvem: str = ""
    fbupdat: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> JudaRecord:
        """Construct from a raw JUDA CSV row dict.

        The CSV uses semicolon delimiters, latin-1 encoding, and NULL sentinel.
        """
        return cls(
            fbptyp=_clean(row.get("FBPTYP", "")),
            fbidnr=_clean(row.get("FBIDNR", "")),
            fbgvnr=_clean(row.get("FBGVNR", "")),
            fbtext=_clean(row.get("FBTEXT", "")),
            fblan=_clean(row.get("FBLAN", "")),
            fbkom=_clean(row.get("FBKOM", "")),
            fbfdbet=_clean(row.get("FBFDBET", "")),
            fbfdrgo=_clean(row.get("FBFDRGO", "")),
            fbanm=_clean(row.get("FBANM", "")),
            fbagrkod2=_clean(row.get("FBAGRKOD2", "")),
            fbbort=_clean(row.get("FBBORT", "")),
            fbupvem=_clean(row.get("FBUPVEM", "")),
            fbupdat=_clean(row.get("FBUPDAT", "")),
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [self.fbtext, self.fbanm, self.fbagrkod2]
        return " ".join(p for p in parts if p)


class RitningRecord(BaseModel):
    """A technical drawing record from FIRA (older) or SIRA (newer) registers."""

    model_config = ConfigDict(populate_by_name=True)

    bnum: str = ""
    blad: str = ""
    avd2: str = ""
    uavd: str = ""
    rtyp2: str = ""
    form2: str = ""
    bdel: str = ""
    datm: str = ""
    ritn: str = ""
    ben1: str = ""
    ben: str = ""
    sakg: str = ""
    sats: str = ""
    dkod: str = ""
    film: str = ""
    aendr: str = ""
    foerv: str = ""
    utlaa: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> RitningRecord:
        """Construct from a FIRA CSV row dict (has header).

        The CSV uses semicolon delimiters, latin-1 encoding, and NULL sentinel.
        """
        return cls(
            bnum=_clean(row.get("BNUM", "")),
            blad=_clean(row.get("BLAD", "")),
            avd2=_clean(row.get("AVD2", "")),
            uavd=_clean(row.get("UAVD", "")),
            rtyp2=_clean(row.get("RTYP2", "")),
            form2=_clean(row.get("FORM2", "")),
            bdel=_clean(row.get("BDEL", "")),
            datm=_clean(row.get("DATM", "")),
            ritn=_clean(row.get("RITN", "")),
            ben1=_clean(row.get("BEN1", "")),
            ben=_clean(row.get("BEN", "")),
            sakg=_clean(row.get("SAKG", "")),
            sats=_clean(row.get("SATS", "")),
            dkod=_clean(row.get("DKOD", "")),
            film=_clean(row.get("FILM", "")),
            aendr=_clean(row.get("AENDR", "")),
            foerv=_clean(row.get("FOERV", "")),
            utlaa=_clean(row.get("UTLAA", "")),
        )

    @classmethod
    def from_csv_list(cls, values: list[str]) -> RitningRecord:
        """Construct from a SIRA headerless CSV row (list of values).

        SIRA files have no header row. The 18 columns match RITNING_FIELDNAMES.
        """
        row = dict(zip(RITNING_FIELDNAMES, values, strict=False))
        return cls.from_csv_row(row)

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [self.ben1, self.ben, self.sakg, self.dkod, self.ritn]
        return " ".join(p for p in parts if p)
