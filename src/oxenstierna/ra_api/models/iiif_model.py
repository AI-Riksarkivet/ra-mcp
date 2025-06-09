import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
