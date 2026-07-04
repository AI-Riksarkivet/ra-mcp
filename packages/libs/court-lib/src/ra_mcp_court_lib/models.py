"""Pydantic models for court records (Domboksregister and Medelstad)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


def _clean(value: str | None) -> str:
    """Convert None to empty string, strip whitespace and surrounding quotes."""
    if value is None:
        return ""
    stripped = value.strip().strip('"')
    return stripped


class DomboksregisterRecord(BaseModel):
    """A person record from the Västra härad court register 1611-1730."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    nr: str = ""
    roll: str = ""
    kategori: str = ""
    titel: str = ""
    fnamn: str = ""
    enamn: str = ""
    socken: str = ""
    plats: str = ""
    anteckning: str = ""
    paragraf_id: str = ""
    datum: str = ""
    arende: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str], paragraf_map: dict[str, dict[str, str]] | None = None) -> DomboksregisterRecord:
        """Construct from a raw Person.csv row dict.

        The CSV uses semicolon delimiters, latin-1 encoding, and all values
        are wrapped in double quotes.

        Args:
            row: Dict from csv.DictReader.
            paragraf_map: Optional mapping from ParagrafId to Paragraf row dict
                          for enriching with datum and arende.
        """
        paragraf_id = _clean(row.get("ParagrafId", ""))
        datum = ""
        arende = ""
        if paragraf_map and paragraf_id in paragraf_map:
            p = paragraf_map[paragraf_id]
            datum = _clean(p.get("Datum", ""))
            arende = _clean(p.get("Arende", ""))

        return cls(
            id=int(_clean(row.get("Id", "0"))),
            nr=_clean(row.get("Nr", "")),
            roll=_clean(row.get("Roll", "")),
            kategori=_clean(row.get("Kategori", "")),
            titel=_clean(row.get("Titel", "")),
            fnamn=_clean(row.get("Fnamn", "")),
            enamn=_clean(row.get("Enamn", "")),
            socken=_clean(row.get("Socken", "")),
            plats=_clean(row.get("Plats", "")),
            anteckning=_clean(row.get("Anteckning", "")),
            paragraf_id=paragraf_id,
            datum=datum,
            arende=arende,
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.fnamn,
            self.enamn,
            self.titel,
            self.socken,
            self.plats,
            self.anteckning,
            self.arende,
        ]
        return " ".join(p for p in parts if p)


class MedelstadRecord(BaseModel):
    """A person record from the Medelstad härad court books 1668-1750."""

    model_config = ConfigDict(populate_by_name=True)

    lopnr: int
    fe_namn_titel: str = ""
    plats_forsamling: str = ""
    norm_fornamn: str = ""
    norm_efternamn: str = ""
    norm_titel: str = ""
    norm_plats: str = ""
    norm_forsamling: str = ""
    ting_dag: str = ""
    ting_typ: str = ""
    mal_nr: str = ""
    mal_typ: str = ""
    mal_referat: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str], maal_map: dict[str, str] | None = None) -> MedelstadRecord:
        """Construct from a raw personposter.csv row dict.

        The CSV uses semicolon delimiters, latin-1 encoding.
        Headers may use Swedish characters (Löpnr).

        Args:
            row: Dict from csv.DictReader.
            maal_map: Optional mapping from Loepnr to Maal_referat string
                      for enriching with case summary text.
        """
        # Handle both Löpnr and Lopnr headers
        lopnr_raw = row.get("Löpnr", "") or row.get("Lopnr", "") or row.get("L\xf6pnr", "")
        lopnr_clean = _clean(lopnr_raw)
        lopnr = int(lopnr_clean) if lopnr_clean else 0

        mal_referat = ""
        if maal_map and lopnr_clean in maal_map:
            mal_referat = maal_map[lopnr_clean]

        return cls(
            lopnr=lopnr,
            fe_namn_titel=_clean(row.get("FEnamnTitel", "")),
            plats_forsamling=_clean(row.get("PlatsFörsamling", "") or row.get("PlatsForsamling", "")),
            norm_fornamn=_clean(row.get("Norm_förnamn", "") or row.get("Norm_fornamn", "")),
            norm_efternamn=_clean(row.get("Normefternamn", "")),
            norm_titel=_clean(row.get("Norm_titel", "")),
            norm_plats=_clean(row.get("Normplats", "")),
            norm_forsamling=_clean(row.get("Norm_församling", "") or row.get("Norm_forsamling", "")),
            ting_dag=_clean(row.get("Ting_dag", "")),
            ting_typ=_clean(row.get("Ting_typ", "")),
            mal_nr=_clean(row.get("Mål_nr", "") or row.get("Mal_nr", "")),
            mal_typ=_clean(row.get("Mål_typ", "") or row.get("Mal_typ", "")),
            mal_referat=mal_referat,
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.norm_fornamn,
            self.norm_efternamn,
            self.norm_titel,
            self.norm_plats,
            self.norm_forsamling,
            self.mal_typ,
            self.mal_referat,
        ]
        return " ".join(p for p in parts if p)
