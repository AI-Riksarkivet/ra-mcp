"""Pydantic models for TORA place data."""

from __future__ import annotations

from pydantic import BaseModel, computed_field


def _parse_coord(value: str) -> float:
    """Parse a coordinate string, handling comma as decimal separator."""
    return float(value.replace(",", "."))


def _extract_id(uri: str) -> str:
    """Extract TORA ID from a URI like 'https://data.riksarkivet.se/tora/9809'."""
    return uri.rsplit("/", 1)[-1]


def _extract_accuracy(uri: str) -> str:
    """Extract accuracy level from URI like '.../coordinateaccuracy/high'."""
    if "/" in uri:
        return uri.rsplit("/", 1)[-1]
    return uri


class ToraPlace(BaseModel):
    """A geocoded historical settlement from TORA."""

    tora_id: str
    name: str
    lat: float
    lon: float
    accuracy: str = ""
    parish: str = ""
    municipality: str = ""
    county: str = ""
    province: str = ""
    wikidata_url: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def tora_url(self) -> str:
        return f"https://data.riksarkivet.se/tora/{self.tora_id}"

    @classmethod
    def from_sparql_binding(cls, binding: dict) -> ToraPlace:
        """Construct from a SPARQL result binding dict.

        Each key maps to a dict with a 'value' key.
        """

        def _get(key: str) -> str:
            entry = binding.get(key)
            if entry is None:
                return ""
            return entry.get("value", "")

        return cls(
            tora_id=_extract_id(_get("place")),
            name=_get("name"),
            lat=_parse_coord(_get("lat")),
            lon=_parse_coord(_get("long")),
            accuracy=_extract_accuracy(_get("accuracy")),
            parish=_get("parish"),
            municipality=_get("municipality"),
            county=_get("county"),
            province=_get("province"),
            wikidata_url=_get("wikidata"),
        )
