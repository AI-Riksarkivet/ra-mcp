import httpx
import re
from typing import List, Optional, Tuple
from oxenstierna.api_models import (
    CollectionInfo,
    Format,
    ManifestInfo,
    Quality,
    SearchResults,
)


class ApiClientError(Exception):
    """Base exception for API client errors."""

    pass


class RateLimitError(ApiClientError):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class RiksarkivetApiClient:
    """Client for interacting with all Riksarkivet APIs following IIIF standards."""

    SEARCH_API_BASE_URL = "https://data.riksarkivet.se/api"
    COLLECTION_API_BASE_URL = "https://lbiiif.riksarkivet.se/collection/arkiv"
    IMAGE_API_BASE_URL = "https://lbiiif.riksarkivet.se"
    PRESENTATION_API_BASE_URL = IMAGE_API_BASE_URL

    def _handle_riksarkivet_response(self, response: httpx.Response) -> None:
        """Handle common Riksarkivet API error responses."""
        if response.status_code == 400:
            raise ApiClientError("Bad Request - incorrect parameters")
        elif response.status_code == 403:
            raise ApiClientError(
                "Forbidden - the resource has no rights statement or is not available"
            )
        elif response.status_code == 404:
            raise ApiClientError("Not Found - missing resource")
        elif response.status_code == 429:
            retry_after = None
            for header_name, header_value in response.headers.items():
                if header_name.lower().startswith("x-ratelimit-reset"):
                    try:
                        retry_after = int(header_value)
                    except ValueError:
                        pass
            raise RateLimitError(
                "Too many requests - rate limit exceeded", retry_after=retry_after
            )
        elif response.status_code == 501:
            raise ApiClientError("Not Implemented - method not implemented")

        response.raise_for_status()

    async def _make_request(self, url: str) -> httpx.Response:
        """Make HTTP request with headers that work reliably with Riksarkivet."""
        headers = {
            "Connection": "close",
            "User-Agent": "curl/8.7.1",
            "Accept": "*/*",
        }

        async with httpx.AsyncClient(http2=False) as client:
            try:
                response = await client.get(url, headers=headers, timeout=30.0)
                self._handle_riksarkivet_response(response)
                return response
            except (RateLimitError, ApiClientError):
                raise
            except httpx.HTTPStatusError as e:
                raise ApiClientError(f"HTTP error: {e}")
            except httpx.RequestError as e:
                raise ApiClientError(f"Request error: {e}")
            except Exception as e:
                raise ApiClientError(f"Unexpected error: {e}")

    async def search_records(
        self, query: str, only_digitized: bool = True, offset: int = 0, limit: int = 100
    ) -> SearchResults:
        """
        Search the Riksarkivet records database.

        Args:
            query: Search terms (e.g., "coffee", "medical records")
            only_digitized: Only return digitized materials (default: True)
            offset: Pagination offset (default: 0)
            limit: Maximum results to return (default: 100)

        Returns:
            SearchResults containing matching records with PIDs
        """
        params = {"text": query, "offset": offset}

        if only_digitized:
            params["only_digitised_materials"] = "true"

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.SEARCH_API_BASE_URL}/records?{query_string}"

        response = await self._make_request(url)

        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            raise ApiClientError(f"Unexpected content type for search: {content_type}")

        search_data = response.json()
        return SearchResults.from_api_response(query, search_data)

    async def get_collection(self, pid: str) -> CollectionInfo:
        """
        Get collection information from a PID.

        Args:
            pid: The PID/UUID from search results

        Returns:
            CollectionInfo containing items (sub-collections and manifests)
        """
        url = f"{self.COLLECTION_API_BASE_URL}/{pid}"
        response = await self._make_request(url)

        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            raise ApiClientError(
                f"Unexpected content type for collection: {content_type}"
            )

        collection_data = response.json()
        return CollectionInfo.from_api_response(pid, collection_data)

    async def get_all_manifests(self, pid: str) -> List[ManifestInfo]:
        """
        Get all manifests from a collection, recursively processing sub-collections.

        This follows the IIIF Presentation API 3.0 pattern and the example code
        that recursively processes collections to find all manifests.

        Args:
            pid: The PID/UUID from search results

        Returns:
            List of ManifestInfo objects for all manifests found
        """
        manifests = []

        async def process_collection_recursive(collection_info: CollectionInfo):
            """Recursively process collections to find manifests (like the example script)."""
            for item in collection_info.items:
                if item.type == "Collection":
                    try:
    
                        sub_pid = item.id.split("/")[-1]
                        sub_collection = await self.get_collection(sub_pid)
                        await process_collection_recursive(sub_collection)
                    except Exception as e:
                        continue
                elif item.type == "Manifest":
                    try:
                        manifest = await self.get_manifest_from_url(item.id)
                        manifests.append(manifest)
                    except Exception as e:
                        continue

        collection = await self.get_collection(pid)
        await process_collection_recursive(collection)

        return manifests

    async def get_manifest_from_url(self, manifest_url: str) -> ManifestInfo:
        """
        Get a IIIF Presentation manifest from its URL.

        Args:
            manifest_url: Full URL to the manifest

        Returns:
            ManifestInfo containing manifest metadata and list of all images
        """
        response = await self._make_request(manifest_url)

        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            raise ApiClientError(
                f"Unexpected content type for manifest: {content_type}"
            )

        manifest_data = response.json()
        return ManifestInfo.from_manifest_data(manifest_data)

    async def get_manifest(self, manifest_id: str) -> ManifestInfo:
        """
        Get a IIIF Presentation manifest by ID.

        Args:
            manifest_id: The manifest identifier (e.g., 'arkis!Z0000054' or just 'Z0000054')

        Returns:
            ManifestInfo containing manifest metadata and list of all images
        """
        if not manifest_id.startswith("arkis!"):
            manifest_id = f"arkis!{manifest_id}"

        url = f"{self.PRESENTATION_API_BASE_URL}/{manifest_id}/manifest"
        return await self.get_manifest_from_url(url)

    def build_image_url(
        self,
        identifier: str,
        region: str,
        size: str,
        rotation: str,
        quality: Quality = Quality.DEFAULT,
        image_format: Format = Format.JPG,
    ) -> str:
        """Build a URL for the IIIF Image API 3.0."""
        return f"{self.IMAGE_API_BASE_URL}/{identifier}/{region}/{size}/{rotation}/{quality.value}.{image_format.value}"

    def build_image_url_from_canvas(
        self,
        canvas_info,
        region: str = "full",
        size: str = "max",
        rotation: str = "0",
        quality: Quality = Quality.DEFAULT,
        image_format: Format = Format.JPG,
    ) -> str:
        """
        Build a IIIF Image URL from a CanvasInfo object.

        Args:
            canvas_info: CanvasInfo object from a manifest
            region, size, rotation, quality, image_format: IIIF parameters

        Returns:
            str: Complete IIIF Image URL
        """
        image_id = canvas_info.image_id
        if not image_id:
            if canvas_info.image_url:
                regex = re.compile(r".*\!(.*)\/full.*")
                match = regex.match(canvas_info.image_url)
                if match:
                    image_id = match.group(1)
                else:
                    raise ApiClientError(
                        f"Could not extract image ID from URL: {canvas_info.image_url}"
                    )
            else:
                raise ApiClientError("No image ID or URL available in canvas info")

        if not image_id.startswith("arkis!"):
            identifier = f"arkis!{image_id}"
        else:
            identifier = image_id

        return self.build_image_url(
            identifier, region, size, rotation, quality, image_format
        )

    def build_image_url_from_manifest(
        self,
        manifest_id: str,
        image_index: int,
        region: str = "full",
        size: str = "max",
        rotation: str = "0",
        quality: Quality = Quality.DEFAULT,
        image_format: Format = Format.JPG,
    ) -> str:
        """
        Build a IIIF Image URL for a specific image in a manifest.

        Note: This method requires the manifest to be fetched first.
        For efficiency, use get_manifest() then build_image_url_from_canvas().

        Args:
            manifest_id: The manifest identifier
            image_index: 1-based index of the image in the manifest
            region, size, rotation, quality, image_format: IIIF parameters

        Returns:
            str: Complete IIIF Image URL
        """

        raise NotImplementedError(
            "For performance reasons, please use: "
            "1. manifest = await client.get_manifest(manifest_id), "
            "2. canvas = manifest.images[image_index - 1], "
            "3. url = client.build_image_url_from_canvas(canvas, ...)"
        )

    def get_thumbnail_url_from_canvas(self, canvas_info, size: str = "300,") -> str:
        """
        Get a thumbnail URL from a canvas.

        Args:
            canvas_info: CanvasInfo object from a manifest
            size: Thumbnail size (default: 300px wide, maintaining aspect ratio)

        Returns:
            str: Thumbnail URL
        """
        return self.build_image_url_from_canvas(
            canvas_info, region="full", size=size, rotation="0"
        )

    def get_common_image_urls_from_canvas(self, canvas_info) -> dict:
        """
        Get common image URL variations from a canvas.

        Args:
            canvas_info: CanvasInfo object from a manifest

        Returns:
            dict: Dictionary with common URL variations
        """
        return {
            "full": self.build_image_url_from_canvas(canvas_info, "full", "max", "0"),
            "thumbnail": self.build_image_url_from_canvas(
                canvas_info, "full", "300,", "0"
            ),
            "medium": self.build_image_url_from_canvas(
                canvas_info, "full", "800,", "0"
            ),
            "square_thumb": self.build_image_url_from_canvas(
                canvas_info, "square", "300,300", "0"
            ),
        }

    async def get_image_data(
        self,
        identifier: str,
        region: str = "full",
        size: str = "max",
        rotation: str = "0",
        quality: Quality = Quality.DEFAULT,
        image_format: Format = Format.JPG,
    ) -> bytes:
        """Get image data using the IIIF Image API."""
        url = self.build_image_url(
            identifier, region, size, rotation, quality, image_format
        )
        response = await self._make_request(url)

        content_type = response.headers.get("content-type", "")
        if not content_type.startswith("image/jpeg"):
            raise ApiClientError(f"Unexpected content type: {content_type}")

        return response.content

    async def get_image_data_from_canvas(self, canvas_info, **kwargs) -> bytes:
        """
        Get image data from a CanvasInfo object.

        This method extracts the image identifier from the canvas and downloads it.
        Follows the pattern from the example script that uses regex to extract image IDs.

        Args:
            canvas_info: CanvasInfo object from a manifest
            **kwargs: Additional IIIF parameters (region, size, rotation, etc.)

        Returns:
            bytes: The image data
        """
        if not canvas_info.image_id:
            if canvas_info.image_url:
                regex = re.compile(r".*\!(.*)\/full.*")
                match = regex.match(canvas_info.image_url)
                if match:
                    image_id = match.group(1)
                else:
                    raise ApiClientError(
                        f"Could not extract image ID from URL: {canvas_info.image_url}"
                    )
            else:
                raise ApiClientError("No image ID or URL available in canvas info")
        else:
            image_id = canvas_info.image_id

        if not image_id.startswith("arkis!"):
            image_identifier = f"arkis!{image_id}"
        else:
            image_identifier = image_id

        return await self.get_image_data(image_identifier, **kwargs)

    async def get_manifest_image_data(
        self,
        manifest_id: str,
        image_index: int,
        region: str = "full",
        size: str = "max",
        rotation: str = "0",
        quality: Quality = Quality.DEFAULT,
        image_format: Format = Format.JPG,
    ) -> Tuple[bytes, str]:
        """
        Get image data for a specific image in a manifest by index.

        Args:
            manifest_id: The manifest identifier (e.g., 'arkis!Z0000054' or 'Z0000054')
            image_index: 1-based index of the image in the manifest
            region, size, rotation, quality, image_format: IIIF parameters

        Returns:
            Tuple of (image_data, image_id)
        """
        manifest = await self.get_manifest(manifest_id)

        if image_index < 1 or image_index > len(manifest.images):
            raise ApiClientError(
                f"Image index {image_index} out of range. Manifest has {len(manifest.images)} images (1-{len(manifest.images)})"
            )

        canvas_info = manifest.images[image_index - 1]

        image_data = await self.get_image_data_from_canvas(
            canvas_info,
            region=region,
            size=size,
            rotation=rotation,
            quality=quality,
            image_format=image_format,
        )

        return image_data, canvas_info.image_id

    async def download_all_images_from_pid(
        self, pid: str
    ) -> List[Tuple[bytes, str, str]]:
        """
        Download all images from all manifests in a collection (like the example script).

        This replicates the functionality of the example download script that:
        1. Gets the collection
        2. Recursively processes sub-collections
        3. Processes manifests to extract image URLs
        4. Downloads all images

        Args:
            pid: The PID/UUID from search results

        Returns:
            List of tuples: (image_data, image_id, manifest_title)
        """
        images = []

        manifests = await self.get_all_manifests(pid)

        for manifest in manifests:
            for canvas in manifest.images:
                try:
                    image_data = await self.get_image_data_from_canvas(canvas)
                    images.append((image_data, canvas.image_id, manifest.title))
                except Exception as e:
                    continue

        return images

    async def get_all_image_urls_from_manifest(
        self,
        manifest_id: str,
        region: str = "full",
        size: str = "max",
        rotation: str = "0",
        quality: Quality = Quality.DEFAULT,
        image_format: Format = Format.JPG,
    ) -> List[Tuple[str, str, int]]:
        """
        Get all image URLs from a manifest.

        Args:
            manifest_id: The manifest identifier
            region, size, rotation, quality, image_format: IIIF parameters

        Returns:
            List of tuples: (image_url, image_id, canvas_index)
        """
        manifest = await self.get_manifest(manifest_id)

        urls = []
        for canvas in manifest.images:
            try:
                url = self.build_image_url_from_canvas(
                    canvas, region, size, rotation, quality, image_format
                )
                urls.append((url, canvas.image_id, canvas.canvas_index))
            except Exception as e:
                continue

        return urls

    async def get_all_image_urls_from_pid(
        self,
        pid: str,
        region: str = "full",
        size: str = "max",
        rotation: str = "0",
        quality: Quality = Quality.DEFAULT,
        image_format: Format = Format.JPG,
    ) -> List[Tuple[str, str, str]]:
        """
        Get all image URLs from all manifests in a collection (like the download script, but URLs).

        Args:
            pid: The PID/UUID from search results
            region, size, rotation, quality, image_format: IIIF parameters

        Returns:
            List of tuples: (image_url, image_id, manifest_title)
        """
        urls = []

        manifests = await self.get_all_manifests(pid)

        for manifest in manifests:
            for canvas in manifest.images:
                try:
                    url = self.build_image_url_from_canvas(
                        canvas, region, size, rotation, quality, image_format
                    )
                    urls.append((url, canvas.image_id, manifest.title))
                except Exception as e:
                    continue

        return urls

    async def get_first_manifest_from_pid(self, pid: str) -> Optional[ManifestInfo]:
        """
        Get the first manifest from a collection PID.

        This is useful for quickly accessing content when you just want
        any manifest from a collection.

        Args:
            pid: The PID/UUID from search results

        Returns:
            First ManifestInfo found, or None if no manifests
        """
        manifests = await self.get_all_manifests(pid)
        return manifests[0] if manifests else None

    async def get_first_image_from_pid(
        self, pid: str
    ) -> Optional[Tuple[bytes, str, str]]:
        """
        Get the first image from a collection PID.

        This is useful for getting a preview image from a collection.

        Args:
            pid: The PID/UUID from search results

        Returns:
            Tuple of (image_data, image_id, manifest_title) or None
        """
        images = await self.download_all_images_from_pid(pid)
        return images[0] if images else None
