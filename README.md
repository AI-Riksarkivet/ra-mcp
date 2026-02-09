<div align="center">
  <img src="assets/logo-rm-bg.png" alt="RA-MCP Logo" width="350">
</div>


# ra-mcp


> **⚠️ Work in Progress (WIP)**
> 
> This repository is the result of two hackathons and is currently under development. It's more of a proof of concept than a production-ready solution. The codebase, documentation, and build processes are being continuously refined.
> 
> **Please note:**
> - Expect changes and breaking updates
> - APIs and interfaces may change without notice
> - Use in production environments at your own risk
> - Contributions and feedback are welcome as we work toward stability

[![Tests](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/ci.yml)
[![CodeQL](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/codeql.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/codeql.yml)
[![Publish](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/publish.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/publish.yml)
[![Secret Leaks](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/trufflehog.yml/badge.svg)](https://github.com/AI-Riksarkivet/ra-mcp/actions/workflows/trufflehog.yml)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Docker Pulls](https://img.shields.io/docker/pulls/riksarkivet/ra-mcp)](https://hub.docker.com/r/riksarkivet/ra-mcp)

[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/AI-Riksarkivet/ra-mcp/badge)](https://scorecard.dev/viewer/?uri=github.com/AI-Riksarkivet/ra-mcp)
[![SLSA 2](https://img.shields.io/badge/SLSA-Level%202-blue?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMyA3VjEyQzMgMTYuNTUgNi44NCAxOS43NCAxMiAyMUMxNy4xNiAxOS43NCAyMSAxNi41NSAyMSAxMlY3TDEyIDJaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4=)](https://slsa.dev/spec/v1.0/levels#build-l2)
[![Signed with Sigstore](https://img.shields.io/badge/Sigstore-Signed-purple?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMyA3VjEyQzMgMTYuNTUgNi44NCAxOS43NCAxMiAyMUMxNy4xNiAxOS43NCAyMSAxNi41NSAyMSAxMlY3TDEyIDJaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4=)](https://www.sigstore.dev/)
[![SBOM](https://img.shields.io/badge/SBOM-SPDX%202.3-green)](https://github.com/AI-Riksarkivet/ra-mcp/releases/latest)

## MCPs for Riksarkivet

A MCP server and command-line tools for searching and browsing transcribed historical documents from the Swedish National Archives (Riksarkivet).

## Features

- **Full-text search** across millions of transcribed historical documents
- **Complete page transcriptions** with accurate text extraction from historical manuscripts
- **Reference-based document browsing** using official archive reference codes
- **Contextual search highlighting** to identify relevant content quickly
- **High-resolution image access** to original document scans via IIIF


## Getting Started

## MCP

Adding ra-mcp with streamable http for ChatGPT or Claude:

url: `https://riksarkivet-ra-mcp.hf.space/mcp`

### Claude Code

```bash
claude mcp add --transport http ra-mcp https://riksarkivet-ra-mcp.hf.space/mcp
```

### IDEs

```bash
cat > mcp.json <<'EOF'
{
  "mcpServers": {
    "ra-mcp": {
      "type": "streamable-http",
      "url": "https://riksarkivet-ra-mcp.hf.space/mcp",
      "note": "ra-mcp server (FastMCP) - via Streamable HTTP"
    }
  }
}
EOF
```

## CLI

Install cli

```bash
uv pip install ra-mcp
# or
uv add ra-mcp
```

## How to Use

### 1. Search for Keywords

Find documents containing specific words or phrases:

```bash
# Basic search
uv run ra search "Stockholm"

# Wildcard search - single character (?)
uv run ra search "St?ckholm"  # Matches "Stockholm", "Stäckholm", etc.

# Wildcard search - multiple characters (*)
uv run ra search "Stock*"     # Matches "Stockholm", "Stocksund", "Stocken", etc.
uv run ra search "St*holm"    # Matches "Stockholm", "Strömholm", etc.
uv run ra search "*holm"      # Matches "Stockholm", "Söderholm", etc.

# Fuzzy search - find similar words
uv run ra search "Stockholm~"   # Matches "Stockholm", "Stokholm", "Stokholms", etc.
uv run ra search "Stockholm~1"  # Matches "Stockholm", "Stokholm" (max edit distance: 1)

# Proximity search - find words within distance
uv run ra search '"Stockholm trolldom"~10'  # "Stockholm" and "trolldom" within 10 words

# Boosting terms - increase relevance of specific terms
uv run ra search "Stockholm^4 trol*"  # Boost "Stockholm" relevance with wildcard
uv run ra search '("Stockholm dom*"^4 Reg*)'  # Boost entire phrase with wildcard

# Boolean operators - combine search terms
uv run ra search "(Stockholm AND trolldom)"  # Both terms required
uv run ra search "(Stockholm OR Göteborg)"  # Either term (or both)
uv run ra search "(Stockholm NOT trolldom)"  # Stockholm but not trolldom
uv run ra search "+Stockholm -trolldom"  # Require Stockholm, exclude trolldom

# Grouping - create complex queries with sub-queries
uv run ra search "((Stockholm OR Göteborg) AND troll*)"  # Either city + häxprocess
uv run ra search "((troll* OR häx*) AND (Stockholm OR Göteborg))"  # Complex grouping
```

**Search Options:**
- `--max N` - Maximum search results (default: 50)
- `--max-display N` - Maximum results to display (default: 20)
- `--max-hits-per-vol N` - Maximum hits to return per volume (default: 3)

**Search Types:**

| Type | Syntax | Example | Description |
|------|--------|---------|-------------|
| **Exact** | `"word"` | `"Stockholm"` | Find exact matches |
| **Wildcard (single)** | `?` | `"St?ckholm"` | Matches any single character |
| **Wildcard (multiple)** | `*` | `"Stock*"` | Matches zero or more characters |
| **Fuzzy** | `~` | `"Stockholm~"` | Finds similar terms based on edit distance (default: 2) |
| **Fuzzy (custom)** | `~N` | `"Stockholm~1"` | Finds similar terms with max edit distance N (0-2) |
| **Proximity** | `"word1 word2"~N` | `"Stockholm trolldom"~10` | Finds terms within N words of each other |
| **Boosting** | `^N` | `"Stockholm^4 trol*"` | Increases relevance of boosted term (default: 1) |
| **Boolean AND** | `AND` or `&&` | `(Stockholm AND trolldom)` | Both terms must be present |
| **Boolean OR** | `OR` or `\|\|` | `(Stockholm OR Göteborg)` | Either term (or both) must be present |
| **Boolean NOT** | `NOT` or `!` | `(Stockholm NOT trolldom)` | First term without second term |
| **Required/Exclude** | `+` / `-` | `+Stockholm -trolldom` | Require term (+) or exclude term (-) |
| **Grouping** | `(...)` | `((Stockholm OR Göteborg) AND troll*)` | Group clauses to form sub-queries |

### 2. Browse Specific Documents

When you find interesting documents, browse them directly:

```bash
# View single page
uv run ra browse "SE/RA/123" --page 5

# View page range
uv run ra browse "SE/RA/123" --pages "1-10"

# View specific pages with search highlighting
uv run ra browse "SE/RA/123" --page "5,7,9" --search-term "Stockholm"
```

**Options:**
- `--page` or `--pages` - Page numbers (e.g., "5", "1-10", "5,7,9")
- `--search-term` - Highlight this term in the text
- `--max-display N` - Maximum pages to display (default: 20)

## Output Features

### 🔍 Search Results
When you run a search, results are presented with:

- **Document grouping** - Related pages grouped together for context
- **Institution & dates** - Archive location and document dates
- **Page numbers** - Specific pages containing your search terms
- **Highlighted snippets** - Preview text with keywords emphasized
- **Browse commands** - Ready-to-run commands for deeper exploration

**Example output:**
```
Document: SE/RA/310187/1 - Kommissorialrätt i Stockholm ang. trolldom
Institution: Riksarkivet i Stockholm/Täby | Date: 1676 - 1677
├─ Page 2: "... **trolldom** ..."
├─ Page 7: "... **Trolldoms** ..."
├─ Page 8: "... **Trolldoms**..."

Browse commands:
  uv run ra browse "SE/RA/310187/1" --page 7 --search-term "trolldom"
  uv run ra browse "SE/RA/310187/1" --pages "2,7,8,52,72" --search-term "trolldom"
```

### 🔗 Available Resources
Each result provides direct access to:

| Resource | Description | Use Case |
|----------|-------------|----------|
| **ALTO XML** | Structured transcription data with precise positioning | Text analysis, data extraction |
| **IIIF Images** | High-resolution document scans with zoom/crop support | Visual inspection, citations |
| **Bildvisning** | Interactive web viewer with search highlighting | Online browsing, sharing |
| **Collections** | IIIF metadata for document series | Understanding document context |

## Examples

### Basic Workflow

1. **Search for a keyword:**
   ```bash
   uv run ra search "Stockholm"
   ```

2. **Browse specific documents:**
   ```bash
   uv run ra browse "SE/RA/123456" --page "10-15" --search-term "Stockholm"
   ```

### Advanced Usage

```bash
# Targeted document browsing
uv run ra browse "SE/RA/760264" --pages "1,5,10-12" --search-term "trolldom"

# Large search with selective display
uv run ra search "trolldom" --max 100 --max-display 30
```

## Technical Details

### Riksarkivet APIs & Data Sources

This tool integrates with multiple Riksarkivet APIs to provide comprehensive access to historical documents:

#### Current Integrations
- **[Search API](https://data.riksarkivet.se/api/records)** - Primary endpoint for full-text search across transcribed materials ([Documentation](https://github.com/Riksarkivet/dataplattform/wiki/Search-API))
- **[IIIF Collections](https://lbiiif.riksarkivet.se/collection/arkiv)** - Access to digitized document collections via IIIF standard ([Documentation](https://github.com/Riksarkivet/dataplattform/wiki/IIIF))
- **[ALTO XML](https://sok.riksarkivet.se/dokument/alto)** - Structured text transcriptions with precise positioning data
- **[IIIF Images](https://lbiiif.riksarkivet.se)** - High-resolution document images with zoom and cropping capabilities
- **[Bildvisning](https://sok.riksarkivet.se/bildvisning)** - Interactive document viewer with search highlighting
- **[OAI-PMH](https://oai-pmh.riksarkivet.se/OAI)** - Metadata harvesting for archive records and references ([Documentation](https://github.com/Riksarkivet/dataplattform/wiki/OAI-PMH))

#### Additional Resources
The [Riksarkivet Data Platform Wiki](https://github.com/Riksarkivet/dataplattform/wiki) provides comprehensive documentation for building additional MCP integrations.

#### Experimental Features
- **[Förvaltningshistorik](https://forvaltningshistorik.riksarkivet.se/Index.htm)** - Semantic search interface (under evaluation)
- **[AI-Riksarkivet HTRflow](https://pypi.org/project/htrflow/)** - Handwritten text recognition pipeline (PyPI package)


## Troubleshooting

### Common Issues

1. **No results found**: Try broader search terms or check spelling
2. **Page not loading**: Some pages may not have transcriptions available
3. **Network timeouts**: Tool includes retry logic, but very slow connections may time out

### Getting Help

```bash
uv run ra --help
uv run ra search --help
uv run ra browse --help
uv run ra serve --help
```


## MCP Server Development

```bash
# clone repo
git clone https://github.com/AI-Riksarkivet/ra-mcp.git
```

### Running the MCP Server

```bash
# Install dependencies
uv sync && uv pip install -e .

# Run the main MCP server (stdio)
cd src/ra_mcp && uv run ra serve

# Run with SSE/HTTP transport on port 8000
cd src/ra_mcp && uv run ra serve --http
```

### Testing with MCP Inspector

Use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) to test and debug the MCP server:

```bash
# Test the server interactively
npx @modelcontextprotocol/inspector uv run ra serve --http
```

The MCP Inspector provides a web interface to test server tools, resources, and prompts during development.

### Testing Docker Images with Dagger

You can test both locally built images and published Docker Hub images using Dagger:

#### Test Locally Built Image

```bash
# Build and test in one command
dagger call test-server --source=.

# Or build first, then get an interactive shell
dagger call build --source=. terminal
```

#### Test Published Docker Hub Image

```bash
# Test a published image with health check
dagger call test-published --image-ref="riksarkivet/ra-mcp:v0.2.3-alpine"

# Start a published image as a service
dagger call serve-published \
  --image-ref="riksarkivet/ra-mcp:v0.2.3-alpine" \
  --port=8000 \
  up --ports 8000:8000
```

**Note:** The `--ports` argument is required to forward the container port to your localhost. Format is `HOST_PORT:CONTAINER_PORT`.

#### Connect Claude Code to Dagger Service

Once the service is running:

```bash
# Add to Claude Code (SSE transport recommended)
claude mcp add --transport sse ra-mcp http://localhost:8000/mcp

# Verify connection
claude mcp list

# Test the connection
claude mcp test ra-mcp
```

#### Stop the Service

- Press `Ctrl+C` in the terminal where the service is running
- Or kill the process: `pkill -f "dagger call serve-published"`

### Building and Publishing with Dagger

The project uses Dagger for containerized builds and publishing to Docker registries. Pre-built images are available on [Docker Hub](https://hub.docker.com/r/riksarkivet/ra-mcp).

#### Prerequisites
- [Dagger CLI](https://docs.dagger.io/install) installed
- Docker registry credentials (for publishing)

#### Available Commands

**Build locally:**
```bash
dagger call build
```

**Run tests:**
```bash
dagger call test
```

**Build and publish to Docker registry:**
```bash
# Set environment variables (both required)
export DOCKER_USERNAME="your-dockerhub-username"
export DOCKER_PASSWORD="your-dockerhub-token-or-password"

# Build and publish with explicit tag
dagger call publish-docker \
  --docker-username=env:DOCKER_USERNAME \
  --docker-password=env:DOCKER_PASSWORD \
  --image-repository="riksarkivet/ra-mcp" \
  --tag="v0.2.0" \
  --source=.

# Or publish using version from pyproject.toml (auto-prefixes with "v")
dagger call publish-docker \
  --docker-username=env:DOCKER_USERNAME \
  --docker-password=env:DOCKER_PASSWORD \
  --image-repository="riksarkivet/ra-mcp" \
  --source=.
```

**Build and publish to PyPI:**
```bash
# Set PyPI token
export PYPI_TOKEN="your-pypi-token"

# Build and publish to PyPI
dagger call publish-pypi \
  --pypi-token=env:PYPI_TOKEN \
  --source=.
```

#### Available Dagger Functions
- `build`: Creates a production-ready container image using the Dockerfile
- `build-local`: Build with custom environment variables and registry settings
- `test`: Runs the test suite (currently skipped until test suite is implemented)
- `publish-docker`: Builds and publishes container image to Docker registry with authentication
- `publish-pypi`: Builds and publishes Python package to PyPI

**Important Notes:**
- Both `DOCKER_USERNAME` and `DOCKER_PASSWORD` must be set as environment variables
- Use the `env:` prefix for Secret parameters (username and password)
- Tests are currently skipped in the publish pipeline until the test suite is implemented
- Tags can be explicit (e.g., `v0.2.0`) or auto-generated from `pyproject.toml`

The Dagger configuration is located in `.dagger/main.go` and provides a complete CI/CD pipeline for the project.

![image](https://github.com/user-attachments/assets/bde56408-5135-4a2a-baf3-f26c32fab9dc)

___

## Current MCP Server Implementation

The MCP server provides access to transcribed historical documents from the Swedish National Archives (Riksarkivet) through three primary tools and two resources:

### 🔧 Available Tools

#### 1. **search_transcribed**
Search for keywords in transcribed materials with pagination support.
```python
search_transcribed(
    keyword="trolldom",          # Search term
    offset=0,                    # Pagination offset (required)
    show_context=False,          # Full page text (default: False for more results)
    max_results=10,              # Maximum results to return
    max_hits_per_document=3      # Max hits per document
)
```

#### 2. **browse_document**
Browse specific pages of a document by reference code.
```python
browse_document(
    reference_code="SE/RA/310187/1",  # Document reference
    pages="7,8,52",                   # Page numbers or ranges
    highlight_term="trolldom",        # Optional keyword highlighting
    max_pages=20                       # Maximum pages to display
)
```


### 📚 Available Resources

- **riksarkivet://contents/table_of_contents** - Complete guide index (Innehållsförteckning)
- **riksarkivet://guide/{filename}** - Specific guide sections (e.g., '01_Domstolar.md', '02_Fangelse.md')

### 🔄 Typical Workflow

1. **Search** → `search_transcribed("trolldom", offset=0)` to find relevant documents
2. **Paginate** → Continue with `offset=50, 100, 150...` for comprehensive discovery
3. **Browse** → Use `browse_document()` to view specific pages with full transcriptions

### 💡 Search Strategy Tips

- Start with `show_context=False` to maximize hit coverage
- Use pagination (increasing offsets) to find all matches
- Enable `show_context=True` only when you need full page text for specific hits
- Browse specific pages for detailed examination with keyword highlighting

___







