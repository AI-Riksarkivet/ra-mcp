"""Pydantic models for SBL (Svenskt biografiskt lexikon) biographical records."""

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


def _parse_int(value: str | None) -> int | None:
    """Parse an integer from string, returning None for NULL/empty/non-numeric."""
    cleaned = _clean(value)
    if not cleaned:
        return None
    try:
        return int(cleaned)
    except ValueError:
        return None


class SBLRecord(BaseModel):
    """A record from Svenskt biografiskt lexikon (SBL)."""

    model_config = ConfigDict(populate_by_name=True)

    article_id: int
    sbl_uri: str = ""
    article_type: str = ""
    volume_number: str = ""
    page_number: str = ""
    surname: str = ""
    given_name: str = ""
    gender: str = ""
    occupation: str = ""
    birth_year_prefix: str = ""
    birth_year: int | None = None
    birth_month: int | None = None
    birth_day: int | None = None
    birth_place: str = ""
    birth_place_comment: str = ""
    birth_place_physical: str = ""
    death_year_prefix: str = ""
    death_year: int | None = None
    death_month: int | None = None
    death_day: int | None = None
    death_place: str = ""
    death_place_comment: str = ""
    death_place_physical: str = ""
    main_article_id: str = ""
    cv: str = ""
    archive: str = ""
    printed_works: str = ""
    sources: str = ""
    article_author: str = ""
    image_files: list[str] = []
    image_descriptions: list[str] = []

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> SBLRecord:
        """Construct an SBLRecord from a raw CSV row dict.

        The CSV uses semicolon delimiters, latin-1 encoding, and the string
        ``NULL`` as a sentinel for missing values.
        """
        # Collect non-empty image files and descriptions (columns 1-9)
        image_files: list[str] = []
        image_descriptions: list[str] = []
        for i in range(1, 10):
            img = _clean(row.get(f"Image file {i}", ""))
            desc = _clean(row.get(f"Image {i} description", ""))
            if img:
                image_files.append(img)
                image_descriptions.append(desc)

        return cls(
            article_id=int(row["Article id"]),
            sbl_uri=_clean(row.get("Svenskt biografiskt lexikon (SBL): URI", "")),
            article_type=_clean(row.get("Type of article", "")),
            volume_number=_clean(row.get("SBL volume number", "")),
            page_number=_clean(row.get("Page number in volume", "")),
            surname=_clean(row.get("Surname", "")),
            given_name=_clean(row.get("Given name", "")),
            gender=_clean(row.get("Gender", "")),
            occupation=_clean(row.get("Occupation, royal title, rank", "")),
            birth_year_prefix=_clean(row.get("Prefix to year of birth", "")),
            birth_year=_parse_int(row.get("Year of birth")),
            birth_month=_parse_int(row.get("Month of birth")),
            birth_day=_parse_int(row.get("Day of birth")),
            birth_place=_clean(row.get("Place of birth", "")),
            birth_place_comment=_clean(row.get("Comment on place of birth", "")),
            birth_place_physical=_clean(row.get("Place of birth (physical location)", "")),
            death_year_prefix=_clean(row.get("Prefix to year of death", "")),
            death_year=_parse_int(row.get("Year of death")),
            death_month=_parse_int(row.get("Month of death")),
            death_day=_parse_int(row.get("Day of death")),
            death_place=_clean(row.get("Place of death", "")),
            death_place_comment=_clean(row.get("Comment on place of death", "")),
            death_place_physical=_clean(row.get("Place of death (physical location)", "")),
            main_article_id=_clean(row.get("Id of main article", "")),
            cv=_clean(row.get("Curriculum vitae", "")),
            archive=_clean(row.get("Archive", "")),
            printed_works=_clean(row.get("Printed works", "")),
            sources=_clean(row.get("Sources", "")),
            article_author=_clean(row.get("Article author", "")),
            image_files=image_files,
            image_descriptions=image_descriptions,
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [
            self.surname,
            self.given_name,
            self.occupation,
            self.cv,
            self.birth_place,
            self.death_place,
            self.archive,
            self.printed_works,
            self.sources,
        ]
        return " ".join(p for p in parts if p)
