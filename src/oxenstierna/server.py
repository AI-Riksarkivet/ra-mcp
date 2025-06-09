from typing import Annotated, Literal, Optional, Tuple
from fastmcp import FastMCP, Image
from fastmcp.exceptions import ToolError
from pydantic import Field

from oxenstierna.ra_api.iiif_client import RiksarkivetIIIFClient
from oxenstierna.ra_api.api_models import Format, Quality
from gradio_client import Client, handle_file

from oxenstierna.ra_api.search_client import RiksarkivetSearchClient


mcp = FastMCP(
    name="riksarkivet_iiif_mcp",
    instructions="""
    This server provides access to the Swedish National Archives (Riksarkivet) through multiple APIs.
    
    SEARCH-BASED WORKFLOW (start here):
    - search_records: Search for content by keywords (e.g., "coffee", "medical records")
    - get_collection_info: Explore what's available in a collection
    - get_all_manifests_from_pid: Get all image batches from a collection
    - get_manifest_info: Get details about a specific image batch
    - get_manifest_image: Download specific images from a batch
    - get_all_images_from_pid: Download all images from a collection
    
    URL BUILDING TOOLS:
    - build_image_url: Build IIIF Image URLs with custom parameters
    - get_image_urls_from_manifest: Get all URLs from an image batch
    - get_image_urls_from_pid: Get all URLs from a collection
    
    TYPICAL WORKFLOW:
    1. search_records("your keywords") → find PIDs
    2. get_collection_info(pid) → see what's available  
    3. get_manifest_info(manifest_id) → explore specific image batch
    4. get_manifest_image(manifest_id, image_index) → download specific image
    
    Example PID: LmOmKigRrH6xqG3GjpvwY3
    """,
)


@mcp.tool()
async def generate_image(
    image_path: str,
    document_type: str = "letter_swedish",
    output_format: str = "alto",
    custom_settings: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Process handwritten text recognition (HTR) on uploaded images and return both file content and download link.

    This function uses machine learning models to automatically detect, segment, and transcribe handwritten text
    from historical documents. It supports different document types and languages, with specialized models
    trained on historical handwriting from the Swedish National Archives (Riksarkivet).

    Args:
        image_path (str): The file path or URL to the image containing handwritten text to be processed.
                         Supports common image formats like JPG, PNG, TIFF.

        document_type (FormatChoices): The type of document and language processing template to use.
                                Available options:
                                - "letter_english": Single-page English handwritten letters
                                - "letter_swedish": Single-page Swedish handwritten letters (default)
                                - "spread_english": Two-page spread English documents with marginalia
                                - "spread_swedish": Two-page spread Swedish documents with marginalia
                                Default: "letter_swedish"

        output_format (FileChoices): The format for the output file containing the transcribed text.
                                Available options:
                                - "txt": Plain text format with line breaks
                                - "alto": ALTO XML format with detailed layout and coordinate information
                                - "page": PAGE XML format with structural markup and positioning data
                                - "json": JSON format with structured text, layout information and metadata
                                Default: "alto"

        custom_settings (Optional[str]): Advanced users can provide custom pipeline configuration as a
                                        JSON string to override the default processing steps.
                                        Default: None (uses predefined configuration for document_type)

        server_name (str): The base URL of the server for constructing download links.
                          Default: "https://gabriel-htrflow-mcp.hf.space"

            Returns:
        Tuple[str, str]: A tuple containing:
            - JSON string with extracted text, file content
            - File path for direct download via gr.File (server_name/gradio_api/file=/tmp/gradio/{temp_folder}/{file_name})
    """
    client = Client("Gabriel/htrflow_mcp")
    result = client.predict(
        image_path=handle_file(image_path),
        document_type=document_type,
        output_format="alto",
        custom_settings="",
        api_name="/htrflow_htr_url",
    )
    return result


iiif_client = RiksarkivetIIIFClient()
search_client = RiksarkivetSearchClient()


# Search API Tools
@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Search Records",
    }
)
async def search_records(
    query: Annotated[
        str,
        Field(
            description="Search terms (e.g., 'coffee', 'medical records', 'church documents')",
            min_length=1,
            max_length=200,
        ),
    ],
    only_digitized: Annotated[
        bool,
        Field(description="Only return digitized materials (default: True)"),
    ] = True,
    offset: Annotated[
        int,
        Field(description="Pagination offset (default: 0)", ge=0),
    ] = 0,
) -> str:
    """
    Search the Riksarkivet records database by keywords.

    Returns search results with PIDs that you can use with other tools.
    This is typically the first step in discovering archival content.
    """
    try:
        results = await search_client.search_records(query, only_digitized, offset)

        if not results.results:
            return f"No results found for '{query}'. Try different keywords or set only_digitized=False."

        info_lines = [
            f"Search Results for '{query}':",
            f"Total hits: {results.total_hits} (showing {results.hits} from offset {results.offset})",
            "",
        ]

        for i, result in enumerate(results.results, 1):
            info_lines.append(f"{i}. {result.caption}")
            info_lines.append(f"   PID: {result.id}")
            info_lines.append(f"   Type: {result.object_type} - {result.type}")
            if result.reference_code:
                info_lines.append(f"   Reference: {result.reference_code}")
            info_lines.append("")

        info_lines.append("Next steps:")
        info_lines.append("- Use get_collection_info(pid) to explore a collection")
        info_lines.append(
            "- Use get_all_manifests_from_pid(pid) to see all image batches"
        )

        return "\n".join(info_lines)

    except Exception as e:
        raise ToolError(f"Unexpected error: {str(e)}")


# Collection API Tools
@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Get Collection Information",
    }
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

        # Separate collections and manifests
        sub_collections = [
            item for item in collection.items if item.type == "Collection"
        ]
        manifests = [item for item in collection.items if item.type == "Manifest"]

        if sub_collections:
            info_lines.append(f"Sub-collections ({len(sub_collections)}):")
            for item in sub_collections[:10]:  # Show first 10
                info_lines.append(f"  - {item.label or 'Untitled'}")
            if len(sub_collections) > 10:
                info_lines.append(f"  ... and {len(sub_collections) - 10} more")
            info_lines.append("")

        if manifests:
            info_lines.append(f"Image batches/manifests ({len(manifests)}):")
            for item in manifests[:10]:  # Show first 10
                info_lines.append(f"  - {item.label or 'Untitled'}")
            if len(manifests) > 10:
                info_lines.append(f"  ... and {len(manifests) - 10} more")
            info_lines.append("")

        info_lines.append("Next steps:")
        info_lines.append(
            f"- Use get_all_manifests_from_pid('{pid}') to get all image batches"
        )
        info_lines.append(
            f"- Use get_all_images_from_pid('{pid}') to download all images"
        )

        return "\n".join(info_lines)

    except Exception as e:
        raise ToolError(f"Unexpected error: {str(e)}")


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Get All Manifests from PID",
    }
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


# Presentation API Tools
@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Get Manifest Information",
    }
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


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Get Manifest Image",
    }
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


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Get All Images from PID",
    }
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


# URL Building Tools
@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Build Image URL",
    }
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


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Get Image URLs from Manifest",
    }
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


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "openWorldHint": True,
        "title": "Get Image URLs from PID",
    }
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


if __name__ == "__main__":
    mcp.run(transport="stdio")
