# ra-mcp  (WIP)

##   MCPs for Riksarkivet 


# debug 

 npx @modelcontextprotocol/inspector uv run python server.py  

 

Alot of mcps can be built with the help of: https://github.com/Riksarkivet/dataplattform/wiki

- Riksarkivet OAIPMH API Integration: https://github.com/Riksarkivet/dataplattform/wiki/OAI-PMH
- Riksarkivet IIIF API Integration: https://github.com/Riksarkivet/dataplattform/wiki/IIIF
- Riksarkivet Search API Integration https://github.com/Riksarkivet/dataplattform/wiki/Search-API
- (new) can we use this? with semantic search: https://forvaltningshistorik.riksarkivet.se/Index.htm <---
- AI-Riksarkviet HTRflow pypi 

![image](https://github.com/user-attachments/assets/bde56408-5135-4a2a-baf3-f26c32fab9dc)

___

Current implementation:
```
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
```
___



