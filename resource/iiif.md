# IIIF APIs Reference (Image API 3.0 & Presentation API 3.0)

## Overview

The IIIF (International Image Interoperability Framework) consists of complementary APIs for delivering and presenting digital content:

- **Image API**: Web service for image manipulation and delivery via URI parameters
- **Presentation API**: JSON-LD format for describing structure, metadata, and presentation of compound digital objects
- **Content Search API**: Full-text search within IIIF resources

## IIIF Image API 3.0

## URI Syntax

### Base URI Template
```
{scheme}://{server}{/prefix}/{identifier}
```

### Image Request URI Template
```
{scheme}://{server}{/prefix}/{identifier}/{region}/{size}/{rotation}/{quality}.{format}
```

### Image Information Request URI Template
```
{scheme}://{server}{/prefix}/{identifier}/info.json
```

## URI Components

| Component | Description |
|-----------|-------------|
| scheme | HTTP or HTTPS protocol |
| server | Host server (may include port number) |
| prefix | Optional path to the service on the host server |
| identifier | Identifier of the requested image (ARK, URN, filename, etc.) |

**Important**: Special characters in identifiers MUST be URI encoded, including slashes (/).

## Image Request Parameters

Parameters must be specified in this exact order: region/size/rotation/quality.format

### Region Parameter

Defines the rectangular portion of the image to return.

| Form | Description | Example |
|------|-------------|---------|
| `full` | Return the complete image | `full` |
| `square` | Return square region (shorter dimension) | `square` |
| `x,y,w,h` | Pixel coordinates (x,y) and dimensions (w,h) | `125,15,120,140` |
| `pct:x,y,w,h` | Percentage coordinates and dimensions | `pct:41.6,7.5,40,70` |

### Size Parameter

Specifies dimensions for scaling the extracted region.

| Form | Description | Example |
|------|-------------|---------|
| `max` | Maximum size available (no upscaling) | `max` |
| `^max` | Maximum size (allows upscaling) | `^max` |
| `w,` | Scale to exact width | `150,` |
| `^w,` | Scale to exact width (allows upscaling) | `^200,` |
| `,h` | Scale to exact height | `,100` |
| `^,h` | Scale to exact height (allows upscaling) | `^,150` |
| `pct:n` | Scale to n percent (max 100%) | `pct:50` |
| `^pct:n` | Scale to n percent (allows upscaling) | `^pct:150` |
| `w,h` | Exact width and height (may distort) | `200,300` |
| `^w,h` | Exact width and height (allows upscaling) | `^250,400` |
| `!w,h` | Best fit within w,h (maintains aspect ratio) | `!200,300` |

### Rotation Parameter

Specifies mirroring and rotation to be applied to the image.

| Form | Description |
|------|-------------|
| `0` | No rotation |
| `90`, `180`, `270` | Clockwise rotation in degrees |
| `!0`, `!90`, etc. | Horizontal mirroring then rotation |

### Quality Parameter

Determines color characteristics of the image.

| Value | Description |
|-------|-------------|
| `default` | Server-determined default quality |
| `color` | Full color image |
| `gray` | Grayscale image |
| `bitonal` | Black and white image |

### Format Parameter

Specifies the output format.

Common formats: `jpg`, `png`, `gif`, `webp`, `tif`

---

## IIIF Presentation API 3.0

### Purpose
The Presentation API provides a standardized way to describe compound digital objects (books, manuscripts, albums, etc.) with their structure, metadata, and presentation instructions. It uses JSON-LD format to enable rich viewing experiences across different client applications.

### Core Resource Types

#### Collection
Ordered list of Manifests and/or other Collections for hierarchical organization.
```json
{
  "@context": "http://iiif.io/api/presentation/3/context.json",
  "id": "https://example.org/collection/books",
  "type": "Collection",
  "label": { "en": ["Book Collection"] },
  "items": [
    {
      "id": "https://example.org/manifest/book1",
      "type": "Manifest",
      "label": { "en": ["Book 1"] }
    }
  ]
}
```

#### Manifest
Describes a single compound object with its structure, metadata, and viewing instructions.
```json
{
  "@context": "http://iiif.io/api/presentation/3/context.json",
  "id": "https://example.org/manifest/book1",
  "type": "Manifest",
  "label": { "en": ["Example Book"] },
  "summary": { "en": ["A description of this book"] },
  "metadata": [
    {
      "label": { "en": ["Author"] },
      "value": { "en": ["Jane Doe"] }
    }
  ],
  "items": [
    {
      "id": "https://example.org/canvas/page1",
      "type": "Canvas",
      "label": { "en": ["Page 1"] },
      "height": 1000,
      "width": 750,
      "items": [
        {
          "id": "https://example.org/page/page1/annopage",
          "type": "AnnotationPage",
          "items": [
            {
              "id": "https://example.org/page/page1/anno",
              "type": "Annotation",
              "motivation": "painting",
              "body": {
                "id": "https://example.org/iiif/page1/full/max/0/default.jpg",
                "type": "Image",
                "format": "image/jpeg",
                "service": [
                  {
                    "id": "https://example.org/iiif/page1",
                    "type": "ImageService3",
                    "profile": "level2"
                  }
                ]
              },
              "target": "https://example.org/canvas/page1"
            }
          ]
        }
      ]
    }
  ]
}
```

#### Canvas
Virtual container representing a view of the object (page, image, time segment) with defined dimensions.
- **Spatial**: Uses `height` and `width` properties
- **Temporal**: Uses `duration` property  
- **Mixed**: Can have all three dimensions

#### Range
Defines structural sections within an object (chapters, movements, articles).
```json
{
  "id": "https://example.org/range/chapter1",
  "type": "Range",
  "label": { "en": ["Chapter 1"] },
  "items": [
    { "id": "https://example.org/canvas/page1", "type": "Canvas" },
    { "id": "https://example.org/canvas/page2", "type": "Canvas" }
  ]
}
```

#### Annotation & Annotation Page
Content is associated with Canvases through Annotations collected in Annotation Pages.
- **Painting motivation**: Content that is part of the Canvas (images, video, audio)
- **Supplementing motivation**: Content derived from the Canvas (transcriptions, translations)
- **Other motivations**: Commentary, tags, etc.

### Essential Properties

#### Required Properties
- **id**: HTTP(S) URI identifier
- **type**: Resource class (Collection, Manifest, Canvas, etc.)
- **label**: Human-readable name (internationalized)

#### Key Descriptive Properties
- **metadata**: Array of label/value pairs for display
- **summary**: Brief description
- **thumbnail**: Representative image(s)
- **provider**: Institution/organization information
- **rights**: License or rights statement URI
- **requiredStatement**: Text that must be displayed (attribution)

#### Technical Properties
- **height/width**: Pixel dimensions for images, aspect ratio for Canvas
- **duration**: Time length in seconds
- **format**: MIME type (e.g., "image/jpeg")
- **profile**: Schema or functionality description
- **viewingDirection**: Display order (left-to-right, right-to-left, etc.)
- **behavior**: Presentation hints (paged, continuous, individuals, etc.)

#### Structural Properties
- **items**: Ordered list of child resources
- **structures**: Top-level Ranges for table of contents
- **annotations**: Commentary Annotation Pages

### Language Internationalization
Properties like `label`, `summary`, and `metadata` use language maps:
```json
{
  "label": {
    "en": ["English Title"],
    "fr": ["Titre Français"],
    "none": ["No Language"]
  }
}
```

### Behavior Values
Control presentation and navigation:

| Behavior | Applies To | Description |
|----------|------------|-------------|
| `auto-advance` | Collections, Manifests, Canvases, Ranges | Automatically proceed to next item |
| `no-auto-advance` | Collections, Manifests, Canvases, Ranges | Do not auto-advance (default) |
| `paged` | Collections, Manifests, Ranges | Page-turning interface |
| `continuous` | Collections, Manifests, Ranges | Virtually stitch views together |
| `individuals` | Collections, Manifests, Ranges | Distinct objects/views (default) |
| `unordered` | Collections, Manifests, Ranges | No inherent order |
| `facing-pages` | Canvases | Canvas shows both parts of opening |
| `sequence` | Ranges | Alternative ordering of Canvases |
| `hidden` | Annotations, etc. | Not rendered by default |

### Viewing Directions
- `left-to-right` (default)
- `right-to-left` 
- `top-to-bottom`
- `bottom-to-top`

---

## Practical Integration Examples

## Practical Integration Examples

### Image API + Presentation API Workflow
1. **Presentation API** provides structure and metadata via Manifests
2. **Image API** delivers actual image content with manipulation capabilities
3. **Annotations** link Image API resources to Canvas positions

```json
{
  "id": "https://example.org/canvas/page1",
  "type": "Canvas",
  "height": 1000,
  "width": 750,
  "items": [{
    "id": "https://example.org/annopage/page1",
    "type": "AnnotationPage",
    "items": [{
      "id": "https://example.org/annotation/page1-image",
      "type": "Annotation",
      "motivation": "painting",
      "body": {
        "id": "https://example.org/iiif/page1/full/max/0/default.jpg",
        "type": "Image",
        "format": "image/jpeg",
        "service": [{
          "id": "https://example.org/iiif/page1",
          "type": "ImageService3",
          "profile": "level2"
        }]
      },
      "target": "https://example.org/canvas/page1"
    }]
  }]
}
```

### Image API Examples

### General Examples
```
# Full image at maximum size, default quality, JPEG format
https://example.org/image-service/abcd1234/full/max/0/default.jpg

# Square region, scaled to 200px width
https://example.org/image-service/abcd1234/square/200,/0/default.jpg

# Specific region by pixels, 50% scale, 90° rotation
https://example.org/image-service/abcd1234/125,15,120,140/pct:50/90/color.png

# Region by percentage, best fit 300x200
https://example.org/image-service/abcd1234/pct:25,25,50,50/!300,200/0/gray.jpg

# Image information document
https://example.org/image-service/abcd1234/info.json
```

### Riksarkivet (Swedish National Archives) Examples

**IIIF Image API 3.0:**
```
# Base URL patterns
https://lbiiif.riksarkivet.se/{image-id}/{region}/{size}/{rotation}/{quality}.jpg
https://lbiiif.riksarkivet.se/v3/{image-id}/{region}/{size}/{rotation}/{quality}.jpg

# Full image examples
https://lbiiif.riksarkivet.se/arkis!R0001216_00005/full/max/0/default.jpg

# Square crop
https://lbiiif.riksarkivet.se/arkis!R0001216_00005/square/max/0/default.jpg

# Region by pixels (x=300, y=300, width=100, height=100)
https://lbiiif.riksarkivet.se/arkis!R0001216_00005/300,300,100,100/max/0/default.jpg

# Scale to fixed width (300px)
https://lbiiif.riksarkivet.se/arkis!R0001216_00005/full/300,/0/default.jpg

# Scale to fixed height (500px)
https://lbiiif.riksarkivet.se/arkis!R0001216_00005/full/,500/0/default.jpg

# Scale to exact dimensions (may distort aspect ratio)
https://lbiiif.riksarkivet.se/arkis!R0001216_00005/full/500,300/0/default.jpg

# 90-degree clockwise rotation
https://lbiiif.riksarkivet.se/arkis!R0001216_00005/full/max/90/default.jpg

# 90-degree rotation with horizontal flip
https://lbiiif.riksarkivet.se/arkis!R0001216_00005/full/max/!90/default.jpg
```

**IIIF Presentation API:**
```
# Manifest for a specific resource
https://lbiiif.riksarkivet.se/{identifier}/manifest

# Example manifest
https://lbiiif.riksarkivet.se/arkis!R0000480/manifest

# Collections (hierarchical organization)
https://lbiiif.riksarkivet.se/collection/riksarkivet
https://lbiiif.riksarkivet.se/collection/amnesomraden  # Subject areas
https://lbiiif.riksarkivet.se/collection/tid           # Time periods

# Collection by archive unit PID
https://lbiiif.riksarkivet.se/collection/arkiv/2Yz2ClKdn2VMeUXQcoZOO6
```

**IIIF Content Search:**
```
# Search within a volume
https://lbiiif.riksarkivet.se/search/arkis!40008511?q=kaffe
https://lbiiif.riksarkivet.se/search/arkis!A0068583?q=juveler
```

### Universal Examples (Any IIIF Server)

## Key Implementation Notes

- Parameters must be in exact order: region/size/rotation/quality.format
- All special characters in identifiers must be URI encoded
- Operations are applied in parameter order: extract region → scale → rotate → adjust quality → convert format
- Servers SHOULD support CORS on image responses
- If region extends beyond image bounds, crop at edges rather than adding empty space
- Zero-dimension regions should return 400 Bad Request

## Error Handling and Rate Limiting

Common HTTP status codes:
- `400 Bad Request` - Invalid parameters
- `403 Forbidden` - Missing rights marking or access denied
- `404 Not Found` - Image/resource not found
- `429 Too Many Requests` - Rate limit exceeded (check X-RateLimit-* headers)
- `501 Not Implemented` - Feature not supported

## CORS Configuration

For external applications, configure CORS headers:
```
# Request header
Origin: https://yourdomain.com

# Response header
Access-Control-Allow-Origin: https://yourdomain.com
```

**Reverse Proxy Setup (recommended for external services):**

Apache HTTP Server:
```apache
ProxyPass /iiif/ https://lbiiif.riksarkivet.se/
ProxyPassReverse /iiif/ https://lbiiif.riksarkivet.se/
Header always set Access-Control-Allow-Origin "*"
```

Nginx:
```nginx
location /iiif/ {
    proxy_pass https://lbiiif.riksarkivet.se/;
    add_header Access-Control-Allow-Origin "*";
}
```

## Programming Examples

### Python: Working with IIIF Manifests and Images
```python
import requests
import json

# Fetch and parse a IIIF Manifest
def get_manifest(manifest_url):
    response = requests.get(manifest_url)
    return response.json()

# Extract all image URLs from a manifest
def extract_image_urls(manifest):
    image_urls = []
    for canvas in manifest.get('items', []):
        for annotation_page in canvas.get('items', []):
            for annotation in annotation_page.get('items', []):
                if annotation.get('motivation') == 'painting':
                    body = annotation.get('body', {})
                    if body.get('type') == 'Image':
                        image_urls.append(body.get('id'))
    return image_urls

# Get image service base URL from image URL
def get_image_service_url(image_url):
    # Remove the Image API parameters to get base service URL
    # e.g., https://example.org/iiif/img1/full/max/0/default.jpg
    # becomes https://example.org/iiif/img1
    parts = image_url.split('/')
    return '/'.join(parts[:-4])  # Remove /region/size/rotation/quality.format

# Generate thumbnail URL using Image API
def create_thumbnail_url(image_url, width=150, height=150):
    service_url = get_image_service_url(image_url)
    return f"{service_url}/full/!{width},{height}/0/default.jpg"

# Example usage
manifest_url = "https://lbiiif.riksarkivet.se/arkis!R0000480/manifest"
manifest = get_manifest(manifest_url)
images = extract_image_urls(manifest)

for img_url in images:
    thumb_url = create_thumbnail_url(img_url)
    print(f"Original: {img_url}")
    print(f"Thumbnail: {thumb_url}")
```

### Python: Download Images from Riksarkivet Collection
```python
import requests
import sys
import json
import zipfile
import re
import os

URL_BASE = 'https://lbiiif.riksarkivet.se/collection/arkiv/'

def process_collection(collection, zip_file):
    for item in collection.get('items', []):
        res = requests.get(item.get('id'))
        if res.status_code == 200:
            item_json = res.json()
            if item.get('type') == 'Collection':
                process_collection(item_json, zip_file)
            else:
                process_manifest(item_json, zip_file)

def process_manifest(manifest, zip_file):
    for canvas in manifest.get('items', []):
        for annotation_page in canvas.get('items', []):
            for annotation in annotation_page.get('items', []):
                image_url = annotation.get('body', {}).get('id')
                if image_url:
                    regex = re.compile('.*\!(.*)\/full.*')
                    result = regex.match(image_url)
                    if result:
                        image_id = result.group(1)
                        try:
                            file_name = f'{image_id}.jpg'
                            print(f'Processing {file_name}')
                            download_file(image_url, file_name)
                            zip_file.write(file_name, file_name)
                            os.remove(file_name)
                        except Exception as e:
                            print(e)

def download_file(url, file_name):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def main():
    if len(sys.argv) > 1:
        pid = sys.argv[1]
        res = requests.get(f'{URL_BASE}{pid}')
        if res.status_code == 200:
            collection = res.json()
            with zipfile.ZipFile(f'{pid}.zip', 'w') as zip_file:
                process_collection(collection, zip_file)
    else:
        print('Usage: download.py <pid>')

if __name__ == "__main__":
    main()
```

### JavaScript: IIIF Viewer Integration
```javascript
// Universal Viewer integration
const manifestUri = 'https://lbiiif.riksarkivet.se/arkis!R0000480/manifest';
const uv = new UV.createUV('#uv-container', { 
  manifestUri: manifestUri,
  configUri: '/uv-config.json'
});

// Mirador viewer integration
const mirador = Mirador.viewer({
  id: 'mirador-container',
  windows: [{
    manifestId: manifestUri,
    canvasId: 'https://lbiiif.riksarkivet.se/arkis!R0000480/canvas/1'
  }]
});

// OpenSeadragon with IIIF Image service
const viewer = OpenSeadragon({
  id: 'osd-container',
  tileSources: {
    '@context': 'http://iiif.io/api/image/3/context.json',
    '@id': 'https://lbiiif.riksarkivet.se/arkis!R0000480_00001',
    'profile': 'level1'
  }
});

// Fetch manifest and display metadata
async function displayManifest(manifestUrl) {
  const response = await fetch(manifestUrl);
  const manifest = await response.json();
  
  // Display basic info
  const title = manifest.label?.en?.[0] || manifest.label?.sv?.[0] || 'Untitled';
  const summary = manifest.summary?.en?.[0] || manifest.summary?.sv?.[0] || '';
  
  document.getElementById('title').textContent = title;
  document.getElementById('summary').textContent = summary;
  
  // Display metadata
  const metadataContainer = document.getElementById('metadata');
  manifest.metadata?.forEach(item => {
    const label = item.label?.en?.[0] || item.label?.sv?.[0] || '';
    const value = item.value?.en?.[0] || item.value?.sv?.[0] || '';
    
    const div = document.createElement('div');
    div.innerHTML = `<strong>${label}:</strong> ${value}`;
    metadataContainer.appendChild(div);
  });
}
```

### Finding Image IDs from Archive Units
1. Get archive unit PID from search interface
2. Fetch collection data: `https://lbiiif.riksarkivet.se/collection/arkiv/{pid}`
3. Extract manifest URLs from `items` array
4. Parse image IDs from manifest image URLs

### IIIF Presentation API Structure

**Collection Response Example:**
```json
{
  "id": "https://lbiiif.riksarkivet.se/collection/arkiv/2Yz2ClKdn2VMeUXQcoZOO6",
  "type": "Collection",
  "label": { "sv": ["1 (1654-1721) - Handlingar rörande förhandlingar..."] },
  "summary": { "sv": ["Referenskod: SE/RA/2113/2113.2/1"] },
  "items": [
    {
      "id": "https://lbiiif.riksarkivet.se/arkis!R0000480/manifest",
      "type": "Manifest",
      "label": { "sv": ["1 (1654-1721) - R0000480 - Handlingar..."] }
    }
  ]
}
```

**Hierarchy:**
- **Collection** → Contains other Collections or Manifests
- **Manifest** → Contains Canvases (individual pages/images)
- **Canvas** → Contains image annotations with Image API URLs

## Common Use Cases

### Image API
- **Thumbnails** - Quick generation of preview images at specific sizes
- **Deep zoom viewers** - Requesting tiles and regions for interactive viewing
- **Responsive images** - Serving appropriate sizes for different devices
- **Image analysis** - Extracting specific regions for processing
- **Print quality** - High-resolution downloads with rotation/cropping

### Presentation API
- **Digital libraries** - Organizing books, manuscripts, and documents
- **Museum collections** - Presenting artworks with metadata and context
- **Archives** - Hierarchical organization of historical materials
- **Educational platforms** - Structured learning materials with annotations
- **Cultural heritage** - Multi-language, multi-institutional content sharing

### Combined Workflows
- **Reading room interfaces** - Full manuscripts with page-turning and zoom
- **Annotation tools** - Transcription and commentary systems
- **Comparative viewing** - Side-by-side analysis of similar materials
- **Mobile apps** - Responsive cultural heritage exploration
- **Research platforms** - Advanced search and analysis tools

## Implementation Notes

### Content Delivery Best Practices
- Use Image API for dynamic image manipulation and delivery
- Use Presentation API for metadata, structure, and viewing instructions
- Combine both APIs for complete digital object presentation
- Implement proper caching strategies for performance
- Consider CDN deployment for global access

### Client Application Patterns
1. **Parse Manifest** → Extract structure and metadata
2. **Render Canvas** → Display individual views/pages
3. **Load Images** → Use Image API services for content
4. **Handle Annotations** → Process transcriptions, translations, comments
5. **Navigate Structure** → Use Ranges for table of contents
6. **Apply Behaviors** → Follow presentation hints (paging, auto-advance, etc.)

### Data Flow
```
Collection → Manifest → Canvas → Annotation → Image Service
     ↓          ↓         ↓          ↓            ↓
  Hierarchy  Metadata  Viewport  Association   Pixels
```

## Implementation Variations

### Riksarkivet (Swedish National Archives) Specifics
**Technical Implementation:**
- **Compliance Level**: Image API Level 1 (basic features)
- **Supported Formats**: JPEG only (`.jpg`)
- **Supported Quality**: `default` only
- **Version Support**: Both IIIF 2.0 and 3.0 APIs
- **Content Types**: 
  - Images: `content-type: image/jpeg`
  - Manifests: `content-type: application/json`
- **Access Rights**: Public digitized archives older than 110 years
- **Rate Limiting**: Enforced with `X-RateLimit-*` headers

**Content Organization:**
- Collections organized by subject (`amnesomraden`) and time (`tid`)
- Archive units identified by persistent IDs (PIDs)
- Manifests correspond to volumes or individual items
- Search integration with full-text OCR content

**API Endpoints:**
- Image API: `https://lbiiif.riksarkivet.se/`
- Collections: `https://lbiiif.riksarkivet.se/collection/`
- Search: `https://lbiiif.riksarkivet.se/search/`

### General IIIF Implementation Patterns

**Compliance Levels (Image API):**
- **Level 0**: Static images with limited manipulation
- **Level 1**: Basic resize, rotation, quality options
- **Level 2**: Full specification support with advanced features

**Common Institution Patterns:**
- **Museums**: Focus on high-quality images with rich metadata
- **Libraries**: Emphasis on text materials with OCR and search
- **Archives**: Hierarchical organization with finding aids
- **Universities**: Research-focused with annotation tools

**Supported IIIF APIs (Typical Implementations):**
- ✅ **Image API 3.0/2.0** - Core image delivery (universal)
- ✅ **Presentation API 3.0** - Metadata and structure (most institutions)
- ✅ **Content Search API 1.0** - Full-text search (text-heavy collections)
- ⚠️ **Authentication API 1.0** - Access control (restricted content)
- ⚠️ **Change Discovery API 1.0** - Update notifications (large institutions)

### Server Technology Stacks

**Popular IIIF Server Software:**
- **Cantaloupe** - Java-based image server (Image API)
- **IIPImage** - C++ high-performance server
- **Loris** - Python image server
- **RIIIF** - Ruby implementation
- **Omeka S** - Content management with IIIF support
- **Samvera/Hyrax** - Digital repository platform
- **DSpace** - Institutional repository with IIIF modules

**Cloud Solutions:**
- **IIIF Hosting** - Managed IIIF services
- **AWS/Azure/GCP** - Serverless IIIF implementations
- **ContentDM** - OCLC's hosted digital collections platform

## Integration with Viewers

### Popular IIIF-Compatible Viewers

**Full-Featured Viewers:**
- **Universal Viewer** - Complete presentation with navigation and metadata
- **Mirador** - Advanced viewer with workspace and comparison features
- **Tify** - Vue.js-based viewer for modern web applications

**Specialized Viewers:**
- **OpenSeadragon** - High-performance pan/zoom for images
- **Leaflet-IIIF** - Map-style tile viewer for large images
- **Annona** - Lightweight annotation-focused viewer

**Implementation Examples:**
```javascript
// Universal Viewer (comprehensive)
const manifestUri = 'https://lbiiif.riksarkivet.se/arkis!R0000480/manifest';
const uv = new UV.createUV('#uv', { manifestUri: manifestUri });

// Mirador (research-focused)
const mirador = Mirador.viewer({
  id: 'mirador',
  windows: [{ manifestId: manifestUri }],
  workspaceControlPanel: { enabled: true }
});

// OpenSeadragon (image-focused)
const viewer = OpenSeadragon({
  id: 'osd',
  tileSources: 'https://example.org/iiif/image1/info.json'
});
```

### Mobile and Responsive Considerations
- Progressive image loading for bandwidth optimization
- Touch-friendly zoom and pan interactions  
- Adaptive metadata display for small screens
- Offline capability for downloaded content
- Platform-specific apps (iOS/Android) using IIIF APIs
