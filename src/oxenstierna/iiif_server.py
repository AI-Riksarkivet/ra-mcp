from typing import Annotated, Literal
from fastmcp import FastMCP, Image
from fastmcp.exceptions import ToolError
from pydantic import Field
from gradio_client import Client

from oxenstierna.ra_api.iiif_client import RiksarkivetIIIFClient
from oxenstierna.ra_api.models.image_model import Format, Quality


iiif_mcp = FastMCP(
    name="iiif_server",
    instructions="""
    🖼️ Riksarkivet IIIF Image Access Server
    
    Access and download digitized historical documents using IIIF standards.
    
    STRUCTURE: PID → Collection → Manifests → Images

    HELP:
    - get_iiif_docs() → Load IIIF documentation and API reference
    
    WORKFLOW:
    1. get_collection_info(pid) → Explore structure
    2. get_all_manifests_from_pid(pid) → Find image batches  
    3. get_manifest_info(manifest_id) → See individual images
    4. get_manifest_image(manifest_id, index) → Download specific image
    
    URL TOOLS:
    - build_image_url() → Custom IIIF transformations
    - get_image_urls_from_manifest() → URLs from image batch
    - get_image_urls_from_pid() → URLs from entire collection
    """,
)


iiif_client = RiksarkivetIIIFClient()


@iiif_mcp.resource(
    "resource://iiif",
    tags={"iiif", "docs"},
)
async def get_iiif_docs() -> str:
    """
    Load IIIF documentation and API reference.
    This provides an overview of available IIIF endpoints and their usage.
    Use this to understand how to interact with the IIIF APIs for accessing
    collections, manifests, and images from the Riksarkivet.
    Returns a string containing the documentation content.
    """

    client = Client("Riksarkivet/iiif_mcp_docs")
    result = client.predict(api_name="/load_iiif_docs")
    return result


@iiif_mcp.tool(
    tags={"collection", "iiif"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Get Collection Information",
    },
)
async def get_collection_info(
    pid: Annotated[
        str,
        Field(
            description="PID/UUID from search results (e.g., 'LmOmKigRrH6xqG3GjpvwY3')",
            min_length=1,
            max_length=100,
        ),
    ],
    max_items_shown: Annotated[
        int,
        Field(
            description="Maximum number of items to display per category (default: 10)",
            ge=1,
            le=50,
        ),
    ] = 10,
) -> str:
    """
    Get information about a collection from a PID.

    Shows what sub-collections and manifests (image batches) are available.
    Use this to explore the structure before downloading content.
    """
    try:
        collection = await iiif_client.get_collection(pid)

        info_lines = [
            f"Collection Information for {pid}:",
            f"Title: {collection.label}",
            f"Total items: {collection.total_items}",
            "",
        ]

        if not collection.items:
            info_lines.append("This collection is empty or has no accessible items.")
            return "\n".join(info_lines)

        sub_collections = [
            item for item in collection.items if item.type == "Collection"
        ]
        manifests = [item for item in collection.items if item.type == "Manifest"]

        def format_item_list(items, category_name):
            """Helper function to format item lists consistently."""
            if not items:
                return []

            lines = [f"{category_name} ({len(items)}):"]

            shown_items = items[:max_items_shown]
            for item in shown_items:
                lines.append(f"  - {item.label or 'Untitled'}")

            if len(items) > max_items_shown:
                remaining = len(items) - max_items_shown
                lines.append(f"  ... and {remaining} more")

            lines.append("")
            return lines

        info_lines.extend(format_item_list(sub_collections, "Sub-collections"))

        info_lines.extend(format_item_list(manifests, "Image batches/manifests"))

        info_lines.extend(
            [
                "Next steps:",
                f"- Use get_all_manifests_from_pid('{pid}') to get all image batches",
                f"- Use get_all_images_from_pid('{pid}') to download all images",
            ]
        )

        return "\n".join(info_lines)

    except Exception as e:
        raise ToolError(f"Unexpected error: {str(e)}")


@iiif_mcp.tool(
    tags={"manifest", "iiif"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Get All Manifests from PID",
    },
)
async def get_all_manifests_from_pid(
    pid: Annotated[
        str,
        Field(
            description="PID/UUID from search results",
            min_length=1,
            max_length=100,
        ),
    ],
) -> str:
    """
    Get all image batches (manifests) from a collection, recursively processing sub-collections.

    This discovers all available image content in the collection hierarchy.
    """
    try:
        manifests = await iiif_client.get_all_manifests(pid)

        if not manifests:
            return f"No manifests found in collection {pid}. The collection may only contain metadata or have no digitized images."

        info_lines = [
            f"Found {len(manifests)} image batch(es) in collection {pid}:",
            "",
        ]

        for i, manifest in enumerate(manifests, 1):
            info_lines.append(f"{i}. {manifest.title}")
            info_lines.append(f"   Manifest ID: {manifest.manifest_id}")
            info_lines.append(f"   Images: {manifest.total_images}")
            if manifest.date_range:
                info_lines.append(f"   Date: {manifest.date_range}")
            if manifest.reference_code:
                info_lines.append(f"   Reference: {manifest.reference_code}")
            info_lines.append("")

        info_lines.append("Next steps:")
        info_lines.append(
            "- Use get_manifest_info(manifest_id) to explore a specific batch"
        )
        info_lines.append(
            "- Use get_manifest_image(manifest_id, image_index) to download specific images"
        )

        return "\n".join(info_lines)

    except Exception as e:
        raise ToolError(f"Unexpected error: {str(e)}")


@iiif_mcp.tool(
    tags={"manifest", "iiif"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Get Manifest Information",
    },
)
async def get_manifest_info(
    manifest_id: Annotated[
        str,
        Field(
            description="Manifest identifier (e.g., 'arkis!Z0000054' or 'Z0000054')",
            min_length=1,
            max_length=100,
        ),
    ],
) -> str:
    """
    Get detailed information about a specific image batch (manifest).

    Shows metadata and lists all individual images with their properties.
    """
    try:
        manifest = await iiif_client.get_manifest(manifest_id)

        info_lines = [
            f"Manifest Information for {manifest_id}:",
            f"Title: {manifest.title}",
            f"Total Images: {manifest.total_images}",
        ]

        if manifest.archive:
            info_lines.append(f"Archive: {manifest.archive}")
        if manifest.series:
            info_lines.append(f"Series: {manifest.series}")
        if manifest.reference_code:
            info_lines.append(f"Reference Code: {manifest.reference_code}")
        if manifest.date_range:
            info_lines.append(f"Date Range: {manifest.date_range}")
        if manifest.rights:
            info_lines.append(f"Rights: {manifest.rights}")

        info_lines.append("\nImages in this batch:")
        for image in manifest.images:
            info_lines.append(
                f"  {image.canvas_index}. {image.label} ({image.image_id}) - {image.width}×{image.height}px"
            )
            if image.viewer_url:
                info_lines.append(f"     View: {image.viewer_url}")

        info_lines.append("\nTo download images:")
        info_lines.append(
            f"Use get_manifest_image('{manifest_id}', image_index) where image_index is 1-{manifest.total_images}"
        )

        if manifest.source_reference:
            info_lines.append("\nSource Reference:")
            info_lines.append(f"{manifest.source_reference}")

        return "\n".join(info_lines)

    except Exception as e:
        raise ToolError(f"Unexpected error: {str(e)}")


@iiif_mcp.tool(
    tags={"manifest", "iiif", "image"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Get Manifest Image",
    },
)
async def get_manifest_image(
    manifest_id: Annotated[
        str,
        Field(
            description="Manifest identifier (e.g., 'arkis!Z0000054' or 'Z0000054')",
            min_length=1,
            max_length=100,
        ),
    ],
    image_index: Annotated[
        int,
        Field(
            description="Index of the image in the batch (1-based). Use get_manifest_info first to see available images.",
            ge=1,
            le=1000,
        ),
    ],
    region: Annotated[
        str,
        Field(
            description="Region to extract: 'full' (entire image), 'square' (centered square), 'x,y,w,h' (pixel coordinates), or 'pct:x,y,w,h' (percentage coordinates)"
        ),
    ] = "full",
    size: Annotated[
        str,
        Field(
            description="Size specification: 'max' (full size), 'w,' (width with aspect ratio), ',h' (height with aspect ratio), or 'w,h' (exact dimensions)"
        ),
    ] = "max",
    rotation: Annotated[
        Literal["0", "90", "180", "270", "!0", "!90", "!180", "!270"],
        Field(
            description="Rotation angle in degrees (0, 90, 180, 270) with optional mirroring (!)"
        ),
    ] = "0",
    quality: Annotated[
        Literal["default"],
        Field(description="Image quality (only 'default' supported by Riksarkivet)"),
    ] = "default",
    image_format: Annotated[
        Literal["jpg"],
        Field(description="Image format (only 'jpg' supported by Riksarkivet)"),
    ] = "jpg",
) -> Image:
    """
    Download a specific image from a batch (manifest) using the IIIF APIs.

    Use get_manifest_info first to see what images are available and their indices.
    """
    try:
        image_data, image_id = await iiif_client.get_manifest_image_data(
            manifest_id,
            image_index,
            region,
            size,
            rotation,
            Quality(quality),
            Format(image_format),
        )

        return Image(data=image_data, format="jpeg")

    except Exception as e:
        raise ToolError(f"Unexpected error retrieving manifest image: {str(e)}")


@iiif_mcp.tool(
    tags={"iiif", "image"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Get All Images from PID",
    },
)
async def get_all_images_from_pid(
    pid: Annotated[
        str,
        Field(
            description="PID/UUID from search results",
            min_length=1,
            max_length=100,
        ),
    ],
    max_images: Annotated[
        int,
        Field(
            description="Maximum number of images to download (default: 50)",
            ge=1,
            le=500,
        ),
    ] = 50,
) -> str:
    """
    Download all images from all manifests in a collection (bulk download).

    Warning: This can download many images and take significant time.
    Use max_images to limit the download size.
    """
    try:
        manifests = await iiif_client.get_all_manifests(pid)

        if not manifests:
            return f"No manifests found in collection {pid}."

        total_images = sum(manifest.total_images for manifest in manifests)

        if total_images > max_images:
            return f"Collection {pid} contains {total_images} images across {len(manifests)} manifests. This exceeds the max_images limit of {max_images}. Use get_manifest_image to download specific images, or increase max_images if needed."

        info_lines = [
            f"Collection {pid} bulk download summary:",
            f"Total manifests: {len(manifests)}",
            f"Total images: {total_images}",
            "",
            "Manifests found:",
        ]

        for manifest in manifests:
            info_lines.append(f"- {manifest.title} ({manifest.total_images} images)")

        info_lines.extend(
            [
                "",
                "To download:",
                "1. Use get_manifest_info(manifest_id) to explore each manifest",
                "2. Use get_manifest_image(manifest_id, image_index) for specific images",
                "3. Or use get_image_urls_from_pid() to get all URLs for external downloading",
            ]
        )

        return "\n".join(info_lines)

    except Exception as e:
        raise ToolError(f"Unexpected error: {str(e)}")


@iiif_mcp.tool(
    tags={"iiif", "image"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Build Image URL",
    },
)
async def build_image_url(
    identifier: Annotated[
        str,
        Field(
            description="Image identifier (e.g., 'arkis!z0000054_00001')",
            min_length=1,
            max_length=100,
        ),
    ],
    region: Annotated[
        str,
        Field(description="Region: 'full', 'square', 'x,y,w,h', or 'pct:x,y,w,h'"),
    ] = "full",
    size: Annotated[
        str,
        Field(description="Size: 'max', 'w,', ',h', or 'w,h'"),
    ] = "max",
    rotation: Annotated[
        Literal["0", "90", "180", "270", "!0", "!90", "!180", "!270"],
        Field(
            description="Rotation: 0, 90, 180, 270 degrees (with optional mirroring !)"
        ),
    ] = "0",
    quality: Annotated[
        Literal["default"],
        Field(description="Quality (only 'default' supported)"),
    ] = "default",
    image_format: Annotated[
        Literal["jpg"],
        Field(description="Format (only 'jpg' supported)"),
    ] = "jpg",
) -> str:
    """
    Build a IIIF Image URL with custom parameters.

    Returns a URL that can be used to access the image with specified transformations.
    """
    try:
        url = iiif_client.build_image_url(
            identifier, region, size, rotation, Quality(quality), Format(image_format)
        )

        return f"IIIF Image URL: {url}"

    except Exception as e:
        raise ToolError(f"Error building URL: {str(e)}")


@iiif_mcp.tool(
    tags={"manifest", "iiif", "image"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Get Image URLs from Manifest",
    },
)
async def get_image_urls_from_manifest(
    manifest_id: Annotated[
        str,
        Field(
            description="Manifest identifier",
            min_length=1,
            max_length=100,
        ),
    ],
    size: Annotated[
        str,
        Field(description="Size for all URLs: 'max', 'w,', ',h', or 'w,h'"),
    ] = "max",
) -> str:
    """
    Get IIIF Image URLs for all images in a manifest.

    Returns a list of URLs that can be used for external downloading or processing.
    """
    try:
        urls = await iiif_client.get_all_image_urls_from_manifest(
            manifest_id, size=size
        )

        if not urls:
            return f"No images found in manifest {manifest_id}."

        info_lines = [
            f"Image URLs from manifest {manifest_id} (size={size}):",
            f"Total images: {len(urls)}",
            "",
        ]

        for url, image_id, canvas_index in urls:
            info_lines.append(f"{canvas_index}. {image_id}")
            info_lines.append(f"   {url}")
            info_lines.append("")

        return "\n".join(info_lines)

    except Exception as e:
        raise ToolError(f"Unexpected error: {str(e)}")


@iiif_mcp.tool(
    tags={"collection", "iiif", "image"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Get Image URLs from PID",
    },
)
async def get_image_urls_from_pid(
    pid: Annotated[
        str,
        Field(
            description="PID/UUID from search results",
            min_length=1,
            max_length=100,
        ),
    ],
    size: Annotated[
        str,
        Field(description="Size for all URLs: 'max', 'w,', ',h', or 'w,h'"),
    ] = "300,",
    max_urls: Annotated[
        int,
        Field(
            description="Maximum number of URLs to return (default: 100)", ge=1, le=1000
        ),
    ] = 100,
) -> str:
    """
    Get IIIF Image URLs for all images in a collection.

    Returns URLs from all manifests in the collection for external downloading.
    """
    try:
        urls = await iiif_client.get_all_image_urls_from_pid(pid, size=size)

        if not urls:
            return f"No images found in collection {pid}."

        if len(urls) > max_urls:
            urls = urls[:max_urls]
            truncated_msg = f" (showing first {max_urls} of {len(urls)} total)"
        else:
            truncated_msg = ""

        info_lines = [
            f"Image URLs from collection {pid} (size={size}){truncated_msg}:",
            "",
        ]

        current_manifest = None
        for url, image_id, manifest_title in urls:
            if manifest_title != current_manifest:
                current_manifest = manifest_title
                info_lines.append(f"## {manifest_title}")
                info_lines.append("")

            info_lines.append(f"- {image_id}: {url}")

        return "\n".join(info_lines)

    except Exception as e:
        raise ToolError(f"Unexpected error: {str(e)}")
