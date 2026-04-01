"""Pydantic models for Aktiebolag records (companies and board members)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


def _clean(value: str | None) -> str:
    """Convert None to empty string, strip whitespace, and treat '-' as null."""
    if value is None:
        return ""
    stripped = value.strip().strip('"')
    if stripped == "-":
        return ""
    return stripped


class AktiebolagRecord(BaseModel):
    """A company record from the Aktiebolag register 1901-1935."""

    model_config = ConfigDict(populate_by_name=True)

    post_id: int
    bolagets_namn: str = ""
    aldre_namn: str = ""
    argang: str = ""
    postadress: str = ""
    bolagets_andamal: str = ""
    styrelsesate: str = ""
    verkstall_dir: str = ""
    aktiekapital: str = ""
    styrelsemedlemmar: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str], styrelse_map: dict[int, str] | None = None) -> AktiebolagRecord:
        """Construct from a raw AKTIEBOLAG.txt row dict.

        The file uses semicolon delimiters, latin-1 encoding, and '-' as null sentinel.

        Args:
            row: Dict from csv.DictReader.
            styrelse_map: Optional mapping from PostID to concatenated board member names.
        """
        post_id_raw = _clean(row.get("PostID", "0"))
        post_id = int(post_id_raw) if post_id_raw else 0

        styrelsemedlemmar = ""
        if styrelse_map and post_id in styrelse_map:
            styrelsemedlemmar = styrelse_map[post_id]

        return cls(
            post_id=post_id,
            bolagets_namn=_clean(row.get("Bolagets_namn", "")),
            aldre_namn=_clean(row.get("Aldre_namn", "")),
            argang=_clean(row.get("Argang", "")),
            postadress=_clean(row.get("Postadress", "")),
            bolagets_andamal=_clean(row.get("Bolagets_andamal", "")),
            styrelsesate=_clean(row.get("Styrelsesate", "")),
            verkstall_dir=_clean(row.get("Verkstall_dir", "")),
            aktiekapital=_clean(row.get("Aktiekapital_stam_A", "")),
            styrelsemedlemmar=styrelsemedlemmar,
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.bolagets_namn,
            self.aldre_namn,
            self.bolagets_andamal,
            self.postadress,
            self.styrelsesate,
            self.verkstall_dir,
            self.styrelsemedlemmar,
        ]
        return " ".join(p for p in parts if p)


class StyrelseRecord(BaseModel):
    """A board member record from the STYRELSEMEDLEMMAR register."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    post_id: int
    styrelsemed: str = ""
    fornamn: str = ""
    titel: str = ""
    kon: str = ""
    bolagets_namn: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str], bolag_map: dict[int, str] | None = None) -> StyrelseRecord:
        """Construct from a raw STYRELSEMEDLEMMAR.txt row dict.

        The file uses semicolon delimiters, latin-1 encoding, and '-' as null sentinel.

        Args:
            row: Dict from csv.DictReader.
            bolag_map: Optional mapping from PostID to company name.
        """
        id_raw = _clean(row.get("Id", "0"))
        record_id = int(id_raw) if id_raw else 0

        post_id_raw = _clean(row.get("PostID", "0"))
        post_id = int(post_id_raw) if post_id_raw else 0

        bolagets_namn = ""
        if bolag_map and post_id in bolag_map:
            bolagets_namn = bolag_map[post_id]

        return cls(
            id=record_id,
            post_id=post_id,
            styrelsemed=_clean(row.get("Styrelsemed", "")),
            fornamn=_clean(row.get("Fornamn", "")),
            titel=_clean(row.get("titel", "")),
            kon=_clean(row.get("Kon", "")),
            bolagets_namn=bolagets_namn,
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.styrelsemed,
            self.fornamn,
            self.titel,
            self.bolagets_namn,
        ]
        return " ".join(p for p in parts if p)
