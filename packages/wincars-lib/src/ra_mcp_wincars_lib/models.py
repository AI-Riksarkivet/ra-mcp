"""Pydantic models for Norrland vehicle registration records (Wincars)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


# Vehicle type display mapping
_TYP_DISPLAY: dict[str, str] = {
    "PB": "Personbil",
    "MC": "Motorcykel",
    "LB": "Lastbil",
    "SL": "Släpvagn",
    "TR": "Traktor",
    "BS": "Buss",
}


def _clean(value: str | None) -> str:
    """Convert NULL / '- -' sentinels or None to empty string, strip whitespace."""
    if value is None:
        return ""
    stripped = value.strip()
    if stripped in ("NULL", "- -"):
        return ""
    return stripped


class WincarsRecord(BaseModel):
    """A vehicle registration record from the Norrland Wincars register 1916-1972."""

    model_config = ConfigDict(populate_by_name=True)

    nreg: str = ""
    typ: str = ""
    fabrikat: str = ""
    aar: str = ""
    freg: str = ""
    mreg: str = ""
    treg: str = ""
    cnr: str = ""
    mnr: str = ""
    status: str = ""
    antag: str = ""
    avreg: str = ""
    hemvist: str = ""
    anm: str = ""
    arkivkod: str = ""
    volym: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> WincarsRecord:
        """Construct a WincarsRecord from a raw CSV row dict.

        The CSV uses semicolon delimiters, latin-1 encoding, NULL and '- -' as sentinels.
        """
        return cls(
            nreg=_clean(row.get("NREG", "")),
            typ=_clean(row.get("TYP", "")),
            fabrikat=_clean(row.get("FABRIKAT", "")),
            aar=_clean(row.get("AAR", "")),
            freg=_clean(row.get("FREG", "")),
            mreg=_clean(row.get("MREG", "")),
            treg=_clean(row.get("TREG", "")),
            cnr=_clean(row.get("CNR", "")),
            mnr=_clean(row.get("MNR", "")),
            status=_clean(row.get("STATUS", "")),
            antag=_clean(row.get("ANTAG", "")),
            avreg=_clean(row.get("AVREG", "")),
            hemvist=_clean(row.get("HEMVIST", "")),
            anm=_clean(row.get("ANM", "")),
            arkivkod=_clean(row.get("ARKISKOD", "")),
            volym=_clean(row.get("VOL", "")),
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.nreg,
            self.fabrikat,
            self.hemvist,
            self.anm,
            self.mreg,
            self.freg,
        ]
        return " ".join(p for p in parts if p)

    @property
    def typ_display(self) -> str:
        """Human-readable vehicle type name."""
        return _TYP_DISPLAY.get(self.typ, self.typ)
