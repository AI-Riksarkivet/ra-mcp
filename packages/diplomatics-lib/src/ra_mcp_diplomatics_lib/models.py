"""Pydantic models for SDHK and MPO medieval document records."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .config import SDHK_MANIFEST_TEMPLATE


class SDHKRecord(BaseModel):
    """A record from the Diplomatarium Suecanum (SDHK) medieval document corpus."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    title: str = ""
    author: str = ""
    date: str = ""
    place: str = ""
    language: str = ""
    summary: str = ""
    comments: str = ""
    edition: str = ""
    seals: str = ""
    original: str = ""
    medieval_copy: str = ""
    postmedieval_copy: str = ""
    medieval_reg: str = ""
    postmedieval_reg: str = ""
    photocopy: str = ""
    printed: str = ""
    print_reg: str = ""
    facsimile: str = ""
    translation: str = ""
    additional: str = ""
    has_manifest: bool = False
    has_transcription: bool = False

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> "SDHKRecord":
        """Construct an SDHKRecord from a raw CSV row dict."""
        return cls(
            id=int(row["Id"]),
            title=row.get("Title", ""),
            author=row.get("Author", ""),
            date=row.get("Date", ""),
            place=row.get("Place", ""),
            language=row.get("Lang", ""),
            summary=row.get("Summary", ""),
            comments=row.get("Comments", ""),
            edition=row.get("Edition", ""),
            seals=row.get("Seals", ""),
            original=row.get("Original", ""),
            medieval_copy=row.get("MedievalCopy", ""),
            postmedieval_copy=row.get("PostmedievalCopy", ""),
            medieval_reg=row.get("MedievalReg", ""),
            postmedieval_reg=row.get("PostmedievalReg", ""),
            photocopy=row.get("Photocopy", ""),
            printed=row.get("Print", ""),
            print_reg=row.get("PrintReg", ""),
            facsimile=row.get("Facsimile", ""),
            translation=row.get("Translation", ""),
            additional=row.get("Additional", ""),
        )

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [self.author, self.summary, self.edition, self.comments, self.seals, self.additional, self.place, self.language, self.date, self.printed, self.title]
        return " ".join(p for p in parts if p)

    @property
    def manifest_url(self) -> str:
        """IIIF manifest URL for this SDHK document (empty if not digitized)."""
        if not self.has_manifest:
            return ""
        return SDHK_MANIFEST_TEMPLATE.format(sdhk_id=self.id)



class MPORecord(BaseModel):
    """A record from the Medieval Provenance Objects (MPO) corpus."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    bildvisning_url: str = ""
    institution: str = ""
    institution_detail: str = ""
    ra_number: str = ""
    ccm_signum: str = ""
    collection: str = ""
    volume_signature: str = ""
    decoration: str = ""
    material: str = ""
    leaf_count: str = ""
    column_count: str = ""
    line_count: str = ""
    line_count2: str = ""
    format_size: str = ""
    writing_space: str = ""
    writing_space2: str = ""
    damage: str = ""
    quire_notes: str = ""
    script: str = ""
    rubrication: str = ""
    notation: str = ""
    staff_lines: str = ""
    notes: str = ""
    manuscript_type: str = ""
    category: str = ""
    title: str = ""
    author: str = ""
    author2: str = ""
    origin_place: str = ""
    use_place: str = ""
    dating: str = ""
    incunabulum: str = ""
    codex: str = ""
    literature: str = ""
    content: str = ""
    iiif_manifest: str = ""

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> "MPORecord":
        """Construct an MPORecord from a raw CSV row dict."""
        return cls(
            id=int(row["signatur"]),
            bildvisning_url=row.get("bildbetrachter", ""),
            institution=row.get("institution", ""),
            institution_detail=row.get("inst2", ""),
            ra_number=row.get("ranr", ""),
            ccm_signum=row.get("ccmsignum", ""),
            collection=row.get("bestandsbezeichnung", ""),
            volume_signature=row.get("bestandssignatur", ""),
            decoration=row.get("buchschmuck", ""),
            material=row.get("beschreibstoff", ""),
            leaf_count=row.get("blattzahl", ""),
            column_count=row.get("spaltenzahl", ""),
            line_count=row.get("zeilenzahl1", ""),
            line_count2=row.get("zeilenzahl2", ""),
            format_size=row.get("format", ""),
            writing_space=row.get("schriftraum1", ""),
            writing_space2=row.get("schriftraum2", ""),
            damage=row.get("schäden", ""),
            quire_notes=row.get("lagenanmerkungen", ""),
            script=row.get("schrift", ""),
            rubrication=row.get("rubrizierung", ""),
            notation=row.get("notation", ""),
            staff_lines=row.get("notenlinien", ""),
            notes=row.get("anmerkungen", ""),
            manuscript_type=row.get("sachtitel", ""),
            category=row.get("sachgruppe", ""),
            title=row.get("titel", ""),
            author=row.get("autor1", ""),
            author2=row.get("autor2", ""),
            origin_place=row.get("entstehungsort", ""),
            use_place=row.get("anwendungsort", ""),
            dating=row.get("datierung", ""),
            incunabulum=row.get("wiegendruck", ""),
            codex=row.get("codex", ""),
            literature=row.get("literatur", ""),
            content=row.get("inhalt", ""),
            iiif_manifest=row.get("iiif_manifest", ""),
        )

    @property
    def manifest_url(self) -> str:
        """IIIF manifest URL (taken directly from the iiif_manifest column)."""
        return self.iiif_manifest

    @property
    def searchable_text(self) -> str:
        """Combined text for full-text search indexing."""
        parts = [self.manuscript_type, self.title, self.author, self.content, self.notes, self.decoration, self.literature, self.damage, self.script, self.category, self.collection, self.dating, self.origin_place, self.use_place, self.material, self.notation, self.ccm_signum, self.codex]
        return " ".join(p for p in parts if p)
