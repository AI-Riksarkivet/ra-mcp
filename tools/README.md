# RA Tool - Riksarkivet Search & Browse

A powerful command-line tool for searching and browsing transcribed historical documents from the Swedish National Archives (Riksarkivet).

## Features

- **Fast keyword search** in transcribed materials
- **Full page context** with transcription display
- **Document browsing** by reference code
- **ALTO XML integration** for accurate text extraction
- **Keyword highlighting** in search results
- **IIIF image access** with direct links
- **Rich formatting** with tables and panels

## Installation

The tool uses [uv script dependencies](https://docs.astral.sh/uv/guides/scripts/) and will automatically install required packages:

```bash
# Make the script executable
chmod +x tools/ra.py

# Run directly (uv will handle dependencies)
./tools/ra.py --help
```

**Dependencies (auto-installed):**
- `requests>=2.31.0` - HTTP client
- `click>=8.1.0` - CLI framework
- `rich>=13.0.0` - Rich text formatting
- `lxml>=4.9.0` - XML parsing

## Commands

### 1. Search Command

Search for keywords across all transcribed materials:

```bash
# Basic search
./tools/ra.py search "Stockholm"

# Search with full page transcriptions
./tools/ra.py search "trolldom" --context --max-pages 5

# Search without document grouping
./tools/ra.py search "vasa" --context --no-grouping --max-pages 3
```

**Options:**
- `--max N` - Maximum search results (default: 50)
- `--max-display N` - Maximum results to display (default: 20)
- `--context` - Show full page transcriptions
- `--max-pages N` - Maximum pages to load context for (default: 10)
- `--no-grouping` - Show pages individually instead of grouped by document

### 2. Browse Command

Browse specific pages by reference code:

```bash
# View single page
./tools/ra.py browse "SE/RA/123" --page 5

# View page range
./tools/ra.py browse "SE/RA/123" --pages "1-10"

# View specific pages with search highlighting
./tools/ra.py browse "SE/RA/123" --page "5,7,9" --search-term "Stockholm"
```

**Options:**
- `--page` or `--pages` - Page numbers (e.g., "5", "1-10", "5,7,9")
- `--search-term` - Highlight this term in the text
- `--max-display N` - Maximum pages to display (default: 20)

### 3. Show Pages Command

Search and immediately display full page transcriptions with context:

```bash
# Find pages with keyword and show full transcriptions
./tools/ra.py show-pages "Stockholm" --max-pages 5

# Include surrounding pages for context
./tools/ra.py show-pages "trolldom" --context-padding 2

# Show pages individually
./tools/ra.py show-pages "vasa" --no-grouping
```

**Options:**
- `--max-pages N` - Maximum pages to display (default: 10)
- `--context-padding N` - Include N pages before/after each hit (default: 1)
- `--no-grouping` - Show pages individually instead of grouped by document

## Output Features

### Search Results
- **Grouped by document** for better context
- **Institution and date** information
- **Page numbers** with search hits
- **Snippet previews** with keyword highlighting
- **Browse command examples** for further exploration

### Full Page Display
- **Complete transcriptions** from ALTO XML
- **Keyword highlighting** in yellow
- **Document metadata** (title, date, hierarchy)
- **Direct links** to images, ALTO XML, and Bildvisning
- **Context pages** marked clearly

### Links Provided
- **ALTO XML** - Full transcription data
- **IIIF Images** - High-resolution document images
- **Bildvisning** - Interactive viewer with search highlighting
- **Collections & Manifests** - IIIF metadata

## Examples

### Basic Workflow

1. **Search for a keyword:**
   ```bash
   ./tools/ra.py search "Stockholm"
   ```

2. **Get full context for interesting hits:**
   ```bash
   ./tools/ra.py search "Stockholm" --context --max-pages 3
   ```

3. **Browse specific documents:**
   ```bash
   ./tools/ra.py browse "SE/RA/123456" --page "10-15" --search-term "Stockholm"
   ```

### Advanced Usage

```bash
# Comprehensive search with context
./tools/ra.py show-pages "handelsbalansen" --context-padding 2 --max-pages 8

# Targeted document browsing
./tools/ra.py browse "SE/RA/760264" --pages "1,5,10-12" --search-term "export"

# Large search with selective display
./tools/ra.py search "järnväg" --max 100 --max-display 30
```

## Technical Details

### Data Sources
- **Search API**: `https://data.riksarkivet.se/api/records`
- **IIIF Collections**: `https://lbiiif.riksarkivet.se/collection/arkiv`
- **ALTO XML**: `https://sok.riksarkivet.se/dokument/alto`
- **Images**: `https://lbiiif.riksarkivet.se` (IIIF Image API)

### Performance
- **Optimized HTTP client** with retry strategies
- **Concurrent processing** where possible
- **Progress indicators** for long operations
- **Graceful error handling** with fallbacks

### Architecture
- **Modular design** with separate clients for each API
- **Rich formatting** with tables and panels
- **URL generation** utilities for different resource types
- **Caching support** for improved performance

## Troubleshooting

### Common Issues

1. **No results found**: Try broader search terms or check spelling
2. **Page not loading**: Some pages may not have transcriptions available
3. **Network timeouts**: Tool includes retry logic, but very slow connections may time out

### Getting Help

```bash
./tools/ra.py --help
./tools/ra.py search --help
./tools/ra.py browse --help
./tools/ra.py show-pages --help
```

For issues with the Riksarkivet APIs or data availability, consult the [Riksarkivet documentation](https://riksarkivet.se/).