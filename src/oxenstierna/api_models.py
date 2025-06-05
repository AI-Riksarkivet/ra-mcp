import re
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """A single search result from the Riksarkivet Search API."""

    id: str = Field(description="PID/UUID for this result")
    object_type: str = Field(description="Type of object (Agent, Archive, etc.)")
    type: str = Field(description="Specific type (FormerOrganization, etc.)")
    caption: str = Field(description="Title/caption of the result")
    reference_code: Optional[str] = Field(
        None, description="Reference code if available"
    )

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "SearchResult":
        """Create SearchResult from API response item."""
        return cls(
            id=data.get("id", ""),
            object_type=data.get("objectType", ""),
            type=data.get("type", ""),
            caption=data.get("caption", ""),
            reference_code=data.get("metadata", {}).get("referenceCode"),
        )


class SearchResults(BaseModel):
    """Search results from the Riksarkivet Search API."""

    total_hits: int = Field(description="Total number of hits")
    hits: int = Field(description="Number of hits returned")
    offset: int = Field(description="Offset for pagination")
    query: str = Field(description="Original search query")
    results: List[SearchResult] = Field(description="List of search results")

    @classmethod
    def from_api_response(cls, query: str, data: Dict[str, Any]) -> "SearchResults":
        """Create SearchResults from API response."""
        results = [
            SearchResult.from_api_response(item) for item in data.get("items", [])
        ]

        return cls(
            total_hits=data.get("totalHits", 0),
            hits=data.get("hits", 0),
            offset=data.get("offset", 0),
            query=query,
            results=results,
        )


class CollectionItem(BaseModel):
    """An item within a collection (can be sub-collection or manifest)."""

    id: str = Field(description="URL/ID of the item")
    type: str = Field(description="Type: 'Collection' or 'Manifest'")
    label: Optional[str] = Field(None, description="Label/title of the item")

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "CollectionItem":
        """Create CollectionItem from API response."""
        label = ""
        label_dict = data.get("label", {})
        if label_dict:
            first_lang = list(label_dict.keys())[0]
            if label_dict[first_lang]:
                label = label_dict[first_lang][0]

        return cls(id=data.get("id", ""), type=data.get("type", ""), label=label)


class CollectionInfo(BaseModel):
    """Information about a collection from the Collection API."""

    pid: str = Field(description="PID/UUID of the collection")
    collection_url: str = Field(description="URL to the collection")
    label: str = Field(description="Title/label of the collection")
    total_items: int = Field(description="Total number of items in collection")
    items: List[CollectionItem] = Field(description="Items in this collection")

    @classmethod
    def from_api_response(cls, pid: str, data: Dict[str, Any]) -> "CollectionInfo":
        """Create CollectionInfo from Collection API response."""
        label_dict = data.get("label", {})
        label = ""
        if label_dict:
            first_lang = list(label_dict.keys())[0]
            if label_dict[first_lang]:
                label = label_dict[first_lang][0]

        items = [
            CollectionItem.from_api_response(item_data)
            for item_data in data.get("items", [])
        ]

        return cls(
            pid=pid,
            collection_url=data.get("id", ""),
            label=label,
            total_items=len(items),
            items=items,
        )


class CanvasInfo(BaseModel):
    """Information about a single image/canvas from a IIIF Presentation manifest."""

    image_id: str = Field(description="The image identifier (e.g., 'z0000054_00001')")
    canvas_index: int = Field(
        description="Index of this image in the manifest (1-based)"
    )
    label: str = Field(description="Label for this image (e.g., 'Bild 1')")
    width: int = Field(ge=1, description="Image width in pixels")
    height: int = Field(ge=1, description="Image height in pixels")
    image_url: str = Field(description="Full URL to the image")
    thumbnail_url: Optional[str] = Field(
        None, description="URL to thumbnail if available"
    )
    viewer_url: Optional[str] = Field(
        None, description="URL to view image in Riksarkivet viewer"
    )

    @classmethod
    def from_canvas_data(cls, canvas_data: Dict[str, Any], index: int) -> "CanvasInfo":
        """Create CanvasInfo from a canvas item in the manifest."""
        image_id = ""
        viewer_url = None

        for metadata in canvas_data.get("metadata", []):
            label_key = (
                list(metadata.get("label", {}).keys())[0]
                if metadata.get("label")
                else ""
            )
            if label_key and metadata["label"][label_key][0] in ["Bildid", "Image ID"]:
                image_id = metadata["value"]["none"][0]
            elif label_key and metadata["label"][label_key][0] in ["Länk", "Link"]:
                viewer_url = metadata["value"]["none"][0]

        image_url = ""
        width = canvas_data.get("width", 0)
        height = canvas_data.get("height", 0)

        for annotation_page in canvas_data.get("items", []):
            for annotation in annotation_page.get("items", []):
                body = annotation.get("body", {})
                if body.get("type") == "Image":
                    image_url = body.get("id", "")
                    if not width:
                        width = body.get("width", 0)
                    if not height:
                        height = body.get("height", 0)

        if not image_id and image_url:
            regex = re.compile(r".*\!(.*)\/full.*")
            match = regex.match(image_url)
            if match:
                image_id = match.group(1)

        label_dict = canvas_data.get("label", {})
        label = ""
        if label_dict:
            first_lang = list(label_dict.keys())[0]
            label = label_dict[first_lang][0] if label_dict[first_lang] else ""

        return cls(
            image_id=image_id,
            canvas_index=index,
            label=label,
            width=width,
            height=height,
            image_url=image_url,
            viewer_url=viewer_url,
        )


class ManifestInfo(BaseModel):
    """Information about a IIIF Presentation manifest (batch/collection of images)."""

    manifest_id: str = Field(description="ID extracted from manifest URL")
    manifest_url: str = Field(description="URL to the manifest")
    title: str = Field(description="Title of the collection/batch")
    reference_code: Optional[str] = Field(None, description="Reference code")
    date_range: Optional[str] = Field(None, description="Date range")
    archive: Optional[str] = Field(None, description="Archive name")
    series: Optional[str] = Field(None, description="Series name")
    rights: Optional[str] = Field(None, description="Rights statement")
    source_reference: Optional[str] = Field(None, description="Source reference")
    total_images: int = Field(description="Total number of images in this manifest")
    images: List[CanvasInfo] = Field(description="List of images in this manifest")

    @classmethod
    def from_manifest_data(cls, manifest_data: Dict[str, Any]) -> "ManifestInfo":
        """Create ManifestInfo from a IIIF Presentation manifest response."""

        manifest_url = manifest_data.get("id", "")

        manifest_id = ""
        if manifest_url:
            manifest_id = (
                manifest_url.rstrip("/").split("/")[-2]
                if "/manifest" in manifest_url
                else ""
            )

        label_dict = manifest_data.get("label", {})
        title = ""
        if label_dict:
            first_lang = list(label_dict.keys())[0]
            title = label_dict[first_lang][0] if label_dict[first_lang] else ""

        archive = None
        series = None
        reference_code = None
        date_range = None
        rights = None
        source_reference = None

        for metadata in manifest_data.get("metadata", []):
            label_key = (
                list(metadata.get("label", {}).keys())[0]
                if metadata.get("label")
                else ""
            )
            if not label_key:
                continue

            label_text = metadata["label"][label_key][0]
            value = (
                metadata["value"]["none"][0]
                if metadata.get("value", {}).get("none")
                else ""
            )

            if label_text in ["Arkiv", "Archive"]:
                archive = value
            elif label_text in ["Serie", "Series"]:
                series = value
            elif label_text in ["Referenskod", "Reference code"]:
                reference_code = value
            elif label_text in ["Datering", "Date"]:
                date_range = value
            elif label_text in ["Rättigheter för digital reproduktion", "Rights"]:
                rights = value
            elif label_text in ["Källhänvisning", "Source reference"]:
                source_reference = value

        images = []
        for i, canvas in enumerate(manifest_data.get("items", []), 1):
            canvas_info = CanvasInfo.from_canvas_data(canvas, i)
            images.append(canvas_info)

        return cls(
            manifest_id=manifest_id,
            manifest_url=manifest_url,
            title=title,
            reference_code=reference_code,
            date_range=date_range,
            archive=archive,
            series=series,
            rights=rights,
            source_reference=source_reference,
            total_images=len(images),
            images=images,
        )


class Region:
    """Represents a region parameter for IIIF Image API 3.0."""

    @staticmethod
    def full() -> str:
        """Get the full image."""
        return "full"

    @staticmethod
    def square() -> str:
        """Get a centered square crop of the image."""
        return "square"

    @staticmethod
    def pixels(x: int, y: int, width: int, height: int) -> str:
        """Get a region by pixel coordinates."""
        if x < 0 or y < 0 or width <= 0 or height <= 0:
            raise ValueError(
                "Region coordinates must be non-negative and dimensions must be positive"
            )
        return f"{x},{y},{width},{height}"

    @staticmethod
    def percentage(x: float, y: float, width: float, height: float) -> str:
        """Get a region by percentage coordinates."""
        if not all(0 <= coord <= 100 for coord in [x, y, width, height]):
            raise ValueError("Percentage coordinates must be between 0 and 100")
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive")
        return f"pct:{x},{y},{width},{height}"


class Size:
    """Represents a size parameter for IIIF Image API 3.0."""

    @staticmethod
    def max() -> str:
        """Get the maximum size (full dimensions)."""
        return "max"

    @staticmethod
    def width(width: int) -> str:
        """Set the width while maintaining the aspect ratio."""
        if width <= 0:
            raise ValueError("Width must be positive")
        return f"{width},"

    @staticmethod
    def height(height: int) -> str:
        """Set the height while maintaining the aspect ratio."""
        if height <= 0:
            raise ValueError("Height must be positive")
        return f",{height}"

    @staticmethod
    def exact(width: int, height: int) -> str:
        """Set exact dimensions (may distort image)."""
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be positive")
        return f"{width},{height}"


class Rotation:
    """Represents a rotation parameter for IIIF Image API 3.0."""

    VALID_DEGREES = [0, 90, 180, 270]

    @staticmethod
    def none() -> str:
        """No rotation."""
        return "0"

    @staticmethod
    def degrees(degrees: int) -> str:
        """Rotate the image by the specified number of degrees."""
        if degrees not in Rotation.VALID_DEGREES:
            raise ValueError(
                f"Riksarkivet only supports rotation by 90-degree intervals: {Rotation.VALID_DEGREES}"
            )
        return str(degrees)

    @staticmethod
    def mirrored(degrees: int = 0) -> str:
        """Mirror the image horizontally and then rotate by the specified degrees."""
        if degrees not in Rotation.VALID_DEGREES:
            raise ValueError(
                f"Riksarkivet only supports rotation by 90-degree intervals: {Rotation.VALID_DEGREES}"
            )
        return f"!{degrees}"


class Quality(str, Enum):
    """Available quality parameters for IIIF Image API 3.0."""

    DEFAULT = "default"


class Format(str, Enum):
    """Available format parameters for IIIF Image API 3.0."""

    JPG = "jpg"
