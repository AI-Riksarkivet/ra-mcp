from typing import Annotated, Literal
from fastmcp import FastMCP, Image
from fastmcp.exceptions import ToolError
from pydantic import Field

from oxenstierna.iiif_client import ApiClientError, RateLimitError, RiksarkivetApiClient
from oxenstierna.api_models import Format, Quality


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

client = RiksarkivetApiClient()


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
        results = await client.search_records(query, only_digitized, offset)

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

    except RateLimitError as e:
        retry_msg = f" Retry after {e.retry_after} seconds." if e.retry_after else ""
        raise ToolError(f"Rate limit exceeded: {str(e)}{retry_msg}")
    except ApiClientError as e:
        raise ToolError(f"Error searching records: {str(e)}")
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
        collection = await client.get_collection(pid)

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

    except RateLimitError as e:
        retry_msg = f" Retry after {e.retry_after} seconds." if e.retry_after else ""
        raise ToolError(f"Rate limit exceeded: {str(e)}{retry_msg}")
    except ApiClientError as e:
        raise ToolError(f"Error getting collection info: {str(e)}")
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
        manifests = await client.get_all_manifests(pid)

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

    except RateLimitError as e:
        retry_msg = f" Retry after {e.retry_after} seconds." if e.retry_after else ""
        raise ToolError(f"Rate limit exceeded: {str(e)}{retry_msg}")
    except ApiClientError as e:
        raise ToolError(f"Error getting manifests: {str(e)}")
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
        manifest = await client.get_manifest(manifest_id)

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

        info_lines.append(f"\nImages in this batch:")
        for image in manifest.images:
            info_lines.append(
                f"  {image.canvas_index}. {image.label} ({image.image_id}) - {image.width}×{image.height}px"
            )
            if image.viewer_url:
                info_lines.append(f"     View: {image.viewer_url}")

        info_lines.append(f"\nTo download images:")
        info_lines.append(
            f"Use get_manifest_image('{manifest_id}', image_index) where image_index is 1-{manifest.total_images}"
        )

        if manifest.source_reference:
            info_lines.append(f"\nSource Reference:")
            info_lines.append(f"{manifest.source_reference}")

        return "\n".join(info_lines)

    except RateLimitError as e:
        retry_msg = f" Retry after {e.retry_after} seconds." if e.retry_after else ""
        raise ToolError(f"Rate limit exceeded: {str(e)}{retry_msg}")
    except ApiClientError as e:
        raise ToolError(f"Error getting manifest info: {str(e)}")
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
        image_data, image_id = await client.get_manifest_image_data(
            manifest_id,
            image_index,
            region,
            size,
            rotation,
            Quality(quality),
            Format(image_format),
        )

        return Image(data=image_data, format="jpeg")

    except RateLimitError as e:
        retry_msg = f" Retry after {e.retry_after} seconds." if e.retry_after else ""
        raise ToolError(f"Rate limit exceeded: {str(e)}{retry_msg}")
    except ApiClientError as e:
        raise ToolError(f"Error retrieving manifest image: {str(e)}")
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
        # Note: This returns a summary instead of actual images due to MCP limitations
        # For actual bulk download, users would need to call get_manifest_image multiple times

        manifests = await client.get_all_manifests(pid)

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

    except RateLimitError as e:
        retry_msg = f" Retry after {e.retry_after} seconds." if e.retry_after else ""
        raise ToolError(f"Rate limit exceeded: {str(e)}{retry_msg}")
    except ApiClientError as e:
        raise ToolError(f"Error getting images from PID: {str(e)}")
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
        url = client.build_image_url(
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
        urls = await client.get_all_image_urls_from_manifest(manifest_id, size=size)

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

    except RateLimitError as e:
        retry_msg = f" Retry after {e.retry_after} seconds." if e.retry_after else ""
        raise ToolError(f"Rate limit exceeded: {str(e)}{retry_msg}")
    except ApiClientError as e:
        raise ToolError(f"Error getting URLs from manifest: {str(e)}")
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
        urls = await client.get_all_image_urls_from_pid(pid, size=size)

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

    except RateLimitError as e:
        retry_msg = f" Retry after {e.retry_after} seconds." if e.retry_after else ""
        raise ToolError(f"Rate limit exceeded: {str(e)}{retry_msg}")
    except ApiClientError as e:
        raise ToolError(f"Error getting URLs from PID: {str(e)}")
    except Exception as e:
        raise ToolError(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    mcp.run(transport="stdio")


