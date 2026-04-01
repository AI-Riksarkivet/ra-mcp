"""Pydantic models for the five Specialsök datasets."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


def _clean(value: str | None) -> str:
    """Convert None/sentinels to empty string, strip whitespace and quotes."""
    if value is None:
        return ""
    stripped = value.strip().strip('"')
    if stripped in ("Borttaget", "NULL", "null"):
        return ""
    return stripped


# ---------------------------------------------------------------------------
# 1. Flygvapenhaverier — Swedish military aviation accidents 1912-2007
# ---------------------------------------------------------------------------


class FlygvapenRecord(BaseModel):
    """A record from the Swedish Air Force accident register 1912-2007."""

    model_config = ConfigDict(populate_by_name=True)

    datum: str = ""
    forband: str = ""
    forband_klartext: str = ""
    fpl_typ: str = ""
    fpl_nr: str = ""
    motor_typ: str = ""
    haveri: str = ""
    bes_ant: str = ""
    ant_omk: str = ""
    grad1: str = ""
    fask1: str = ""
    sammanfattning: str = ""
    havplats: str = ""
    klassning: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> FlygvapenRecord:
        """Construct from a raw CSV row dict (semicolon-delimited, latin-1)."""
        return cls(
            datum=_clean(row.get("Datum", "")),
            forband=_clean(row.get("Förband", "") or row.get("Forband", "")),
            forband_klartext=_clean(row.get("Förband klartext", "") or row.get("Forband klartext", "")),
            fpl_typ=_clean(row.get("FplTyp", "")),
            fpl_nr=_clean(row.get("FplNr", "")),
            motor_typ=_clean(row.get("MotorTyp", "")),
            haveri=_clean(row.get("Haveri", "")),
            bes_ant=_clean(row.get("BesAnt", "")),
            ant_omk=_clean(row.get("AntOmk", "")),
            grad1=_clean(row.get("Grad1", "")),
            fask1=_clean(row.get("Fask1", "")),
            sammanfattning=_clean(row.get("Sammanfattning", "")),
            havplats=_clean(row.get("Havplats", "")),
            klassning=_clean(row.get("Klassning", "")),
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [self.fpl_typ, self.forband_klartext, self.sammanfattning, self.havplats, self.motor_typ]
        return " ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# 2. Fångrullor — Östersund prison records 1810-1900
# ---------------------------------------------------------------------------

# The CSV has NO header row — these are the assigned field names.
FANGRULLOR_FIELDNAMES = ["Efternamn", "Fornamn", "Alder", "Hemort", "Brott", "Nummer", "Ar"]


class FangrullorRecord(BaseModel):
    """A record from Östersund prison rolls 1810-1900."""

    model_config = ConfigDict(populate_by_name=True)

    efternamn: str = ""
    fornamn: str = ""
    alder: str = ""
    hemort: str = ""
    brott: str = ""
    nummer: str = ""
    ar: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> FangrullorRecord:
        """Construct from a row dict with manually assigned fieldnames."""
        return cls(
            efternamn=_clean(row.get("Efternamn", "")),
            fornamn=_clean(row.get("Fornamn", "")),
            alder=_clean(row.get("Alder", "")),
            hemort=_clean(row.get("Hemort", "")),
            brott=_clean(row.get("Brott", "")),
            nummer=_clean(row.get("Nummer", "")),
            ar=_clean(row.get("Ar", "")),
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [self.efternamn, self.fornamn, self.hemort, self.brott]
        return " ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# 3. Kurhuset — Venereal disease hospital patients 1817-1866
# ---------------------------------------------------------------------------


class KurhusetRecord(BaseModel):
    """A patient record from the Kurhuset (venereal disease hospital) 1817-1866."""

    model_config = ConfigDict(populate_by_name=True)

    nummer: str = ""
    inskrivningsdatum: str = ""
    fornamn: str = ""
    efternamn: str = ""
    alder: str = ""
    titel: str = ""
    familj: str = ""
    hemort_by: str = ""
    hemort_socken: str = ""
    sjukdom: str = ""
    sjukdomsbeskrivning: str = ""
    sjukdomsbehandling: str = ""
    utskrivningsdatum: str = ""
    utskrivningsstatus: str = ""
    vardtid: str = ""
    anmarkning: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> KurhusetRecord:
        """Construct from a raw CSV row dict (semicolon-delimited, latin-1, Swedish headers)."""
        return cls(
            nummer=_clean(row.get("NUMMER", "")),
            inskrivningsdatum=_clean(row.get("INSKRIVNINGSDATUM", "")),
            fornamn=_clean(row.get("FÖRNAMN", "") or row.get("FORNAMN", "")),
            efternamn=_clean(row.get("EFTERNAMN", "")),
            alder=_clean(row.get("ÅLDER", "") or row.get("ALDER", "")),
            titel=_clean(row.get("TITEL", "")),
            familj=_clean(row.get("FAMILJ", "")),
            hemort_by=_clean(row.get("BY", "") or row.get("HEMORT", "")),
            hemort_socken=_clean(row.get("SOCKEN", "")),
            sjukdom=_clean(row.get("SJUKDOM", "")),
            sjukdomsbeskrivning=_clean(row.get("SJUKDOMSBESKRIVNING", "")),
            sjukdomsbehandling=_clean(row.get("SJUKDOMSBEHANDLING", "")),
            utskrivningsdatum=_clean(row.get("UTSKRIVNINGSDATUM", "")),
            utskrivningsstatus=_clean(row.get("UTSKRIVNINGSSTATUS", "")),
            vardtid=_clean(row.get("VÅRDTID", "") or row.get("VARDTID", "")),
            anmarkning=_clean(row.get("ANMÄRKNING", "") or row.get("ANMARKNING", "")),
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.fornamn,
            self.efternamn,
            self.titel,
            self.hemort_by,
            self.hemort_socken,
            self.sjukdom,
            self.sjukdomsbeskrivning,
        ]
        return " ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# 4. Presskonferenser — Government press conferences 1993-2017
# ---------------------------------------------------------------------------


class PressRecord(BaseModel):
    """A government press conference record 1993-2017."""

    model_config = ConfigDict(populate_by_name=True)

    v_ra_nr: str = ""
    datum: str = ""
    aar: str = ""
    titel: str = ""
    innehaall: str = ""
    arkivbildare: str = ""
    anmaerkning: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> PressRecord:
        """Construct from a raw CSV row dict (semicolon-delimited, latin-1)."""
        return cls(
            v_ra_nr=_clean(row.get("V_RA_NR", "")),
            datum=_clean(row.get("DATUM", "")),
            aar=_clean(row.get("AAR", "")),
            titel=_clean(row.get("Titel", "")),
            innehaall=_clean(row.get("INNEHAALL", "") or row.get("INNEHÅLL", "")),
            arkivbildare=_clean(row.get("ARKIVBILDARE_SAMLING", "")),
            anmaerkning=_clean(row.get("ANMAERKNING", "") or row.get("ANMÄRKNING", "")),
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [self.titel, self.innehaall, self.anmaerkning]
        return " ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# 5. Videobutiker — Video rental stores 1991-1994
# ---------------------------------------------------------------------------


class VideoRecord(BaseModel):
    """A video rental store record 1991-1994."""

    model_config = ConfigDict(populate_by_name=True)

    reg_nr: str = ""
    laen: str = ""
    kommun: str = ""
    butiksnamn: str = ""
    firmanamn: str = ""
    aktiv: str = ""
    besoeksadress: str = ""
    ort: str = ""
    landsdel: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> VideoRecord:
        """Construct from a raw CSV row dict (semicolon-delimited, latin-1).

        Sentinel values 'Borttaget' and 'NULL' are cleaned to empty strings.
        """
        return cls(
            reg_nr=_clean(row.get("Reg_nr", "")),
            laen=_clean(row.get("Laen", "")),
            kommun=_clean(row.get("Kommun", "")),
            butiksnamn=_clean(row.get("Butiksnamn", "")),
            firmanamn=_clean(row.get("Firmanamn", "")),
            aktiv=_clean(row.get("Aktiv", "")),
            besoeksadress=_clean(row.get("Besoeksadress", "")),
            ort=_clean(row.get("Ort", "")),
            landsdel=_clean(row.get("Landsdel", "")),
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [self.butiksnamn, self.firmanamn, self.kommun, self.laen, self.ort]
        return " ".join(p for p in parts if p)
