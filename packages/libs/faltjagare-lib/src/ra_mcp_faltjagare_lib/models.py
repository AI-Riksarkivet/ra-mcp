"""Pydantic models for Fältjägare (Jämtland field regiment) soldier records."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


def _clean(value: str | None) -> str:
    """Convert NULL sentinel, '<okänd>', or None to empty string, strip whitespace."""
    if value is None:
        return ""
    stripped = value.strip()
    if stripped in ("", "NULL", "<okänd>"):
        return ""
    return stripped


class FaltjagareRecord(BaseModel):
    """A record from the Jämtland field regiment soldier registry."""

    model_config = ConfigDict(populate_by_name=True)

    soldatnamn: str = ""
    foernamn: str = ""
    familjenamn: str = ""
    kompani: str = ""
    befattning: str = ""
    rotens_socken: str = ""
    region: str = ""
    from_tjaenst: str = ""
    till_tjaenst: str = ""
    foedelsedatum: str = ""
    foedelsesocken: str = ""
    foedelseregion: str = ""
    platsen_stupade: str = ""
    doedsort: str = ""
    doedsdatum: str = ""
    oevrig_information: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> FaltjagareRecord:
        """Construct a FaltjagareRecord from a raw CSV row dict.

        The CSV uses semicolon delimiters, latin-1 encoding, and the string
        ``NULL`` as a sentinel for missing values. Column headers may have
        trailing whitespace.
        """
        # Strip keys to handle trailing whitespace in column headers
        r = {k.strip(): v for k, v in row.items()}
        return cls(
            soldatnamn=_clean(r.get("Soldatnamn", "")),
            foernamn=_clean(r.get("Foernamn", "")),
            familjenamn=_clean(r.get("Soldatens_familjenamn", "")),
            kompani=_clean(r.get("Kompani", "")),
            befattning=_clean(r.get("Befattning_regemente", "")),
            rotens_socken=_clean(r.get("Rotens_socken", "")),
            region=_clean(r.get("Region", "")),
            from_tjaenst=_clean(r.get("From_tjaenst", "")),
            till_tjaenst=_clean(r.get("Slutdatum_tjaenstgoeringsperiod", "")),
            foedelsedatum=_clean(r.get("Soldatens_foedelsedatum", "")),
            foedelsesocken=_clean(r.get("Soldatens_foedelsesocken", "")),
            foedelseregion=_clean(r.get("Soldatens_foedelseregion", "")),
            platsen_stupade=_clean(r.get("Platsen_stupade", "")),
            doedsort=_clean(r.get("Soldatens_doedsort", "")),
            doedsdatum=_clean(r.get("Soldatens_doedsdatum", "")),
            oevrig_information=_clean(r.get("Oevrig_information", "")),
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.soldatnamn,
            self.foernamn,
            self.familjenamn,
            self.kompani,
            self.befattning,
            self.rotens_socken,
            self.region,
            self.foedelsesocken,
            self.oevrig_information,
        ]
        return " ".join(p for p in parts if p)
