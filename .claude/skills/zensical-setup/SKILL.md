---
name: zensical-setup
description: >
  Guide for setting up and configuring Zensical documentation sites.
  Use when: create documentation site, configure zensical.toml, set up
  navigation, change theme colors, configure fonts, add analytics,
  deploy docs site, GitHub Pages, GitLab Pages, mkdocs.yml migration,
  customize Zensical theme, template overrides, add CSS or JavaScript.
---

# Zensical Site Setup & Configuration

Zensical is a modern static site generator for project documentation, built by
the creators of Material for MkDocs. It uses TOML configuration (`zensical.toml`)
and supports `mkdocs.yml` for migration. This skill covers installation,
configuration, theming, navigation, deployment, and customization.

## Quick Start

```bash
# Install
python3 -m venv .venv && source .venv/bin/activate && pip install zensical
# Or with uv:
uv init && uv add --dev zensical

# Create project
zensical new .

# Preview
zensical serve

# Build
zensical build
```

Generated structure:
```
.
├─ .github/        # GitHub Actions workflow
├─ docs/
│  ├─ index.md
│  └─ markdown.md
└─ zensical.toml
```

## Configuration File

Zensical uses `zensical.toml` (recommended) or `mkdocs.yml` (for migration).
All settings live under the `[project]` scope.

### Essential Settings

```toml
[project]
site_name = "My Site"                    # Required
site_url = "https://example.com"         # Strongly recommended
site_description = "Project docs"        # For HTML meta
site_author = "Jane Doe"                 # For HTML meta
copyright = "&copy; 2025 Jane Doe"       # Footer copyright
docs_dir = "docs"                        # Source directory (default)
site_dir = "site"                        # Output directory (default)
use_directory_urls = true                # Pretty URLs (default)
dev_addr = "localhost:8000"              # Dev server address (default)
```

### Theme Variant

Two variants: `modern` (default, fresh design) and `classic` (matches Material for MkDocs).

```toml
[project.theme]
variant = "classic"   # Use "classic" for Material for MkDocs look
```

## Navigation

### Automatic Navigation

By default, Zensical generates navigation from the folder structure.

### Explicit Navigation

```toml
[project]
nav = [
  { "Home" = "index.md" },
  { "About" = [
    "about/index.md",
    "about/vision.md",
    "about/team.md"
  ]},
  { "GitHub Repo" = "https://github.com/org/repo" }  # External links
]
```

### Navigation Features

Enable features under `[project.theme]`:

```toml
[project.theme]
features = [
  # Instant navigation (SPA-like behavior, requires site_url)
  "navigation.instant",
  "navigation.instant.prefetch",     # Prefetch on hover
  "navigation.instant.progress",     # Progress bar on slow connections

  # Navigation structure
  "navigation.tabs",                 # Top-level sections as tabs
  "navigation.tabs.sticky",          # Sticky tabs on scroll
  "navigation.sections",             # Render top-level as groups
  "navigation.expand",               # Expand all subsections by default
  "navigation.indexes",              # Section index pages
  "navigation.path",                 # Breadcrumb navigation
  "navigation.prune",                # Reduce HTML size ~33%
  "navigation.top",                  # Back-to-top button
  "navigation.footer",               # Previous/next page links in footer
  "navigation.tracking",             # Update URL with active anchor

  # Table of contents
  "toc.follow",                      # Auto-scroll TOC to active anchor
  "toc.integrate",                   # TOC in left sidebar (incompatible with navigation.indexes)

  # Instant previews (experimental, headerlinks only)
  # Configured via markdown extension, see below
]
```

**Incompatibilities:**
- `navigation.prune` ↔ `navigation.expand`
- `navigation.indexes` ↔ `toc.integrate`

### Instant Previews

```toml
[project.markdown_extensions.zensical.extensions.preview]
configurations = [
  { targets.include = ["setup/extensions/*", "customization.md"] }
]
```

### Hiding Sidebars (per page, via front matter)

```yaml
---
hide:
  - navigation
  - toc
  - path
  - footer
  - tags
  - feedback
---
```

## Colors

### Color Scheme

```toml
[project.theme.palette]
scheme = "default"     # Light mode
# scheme = "slate"     # Dark mode
primary = "indigo"     # Header/sidebar/links color
accent = "indigo"      # Interactive elements color
```

**Available primary colors:** red, pink, purple, deep-purple, indigo, blue,
light-blue, cyan, teal, green, light-green, lime, yellow, amber, orange,
deep-orange, brown, grey, blue-grey, black, white, custom.

**Available accent colors:** red, pink, purple, deep-purple, indigo, blue,
light-blue, cyan, teal, green, light-green, lime, yellow, amber, orange,
deep-orange.

### Color Palette Toggle (light/dark switch)

```toml
[[project.theme.palette]]
scheme = "default"
toggle.icon = "lucide/sun"
toggle.name = "Switch to dark mode"

[[project.theme.palette]]
scheme = "slate"
toggle.icon = "lucide/moon"
toggle.name = "Switch to light mode"
```

### System Preference + Automatic Mode

```toml
[[project.theme.palette]]
media = "(prefers-color-scheme)"
toggle.icon = "lucide/sun-moon"
toggle.name = "Switch to light mode"

[[project.theme.palette]]
media = "(prefers-color-scheme: light)"
scheme = "default"
toggle.icon = "lucide/sun"
toggle.name = "Switch to dark mode"

[[project.theme.palette]]
media = "(prefers-color-scheme: dark)"
scheme = "slate"
toggle.icon = "lucide/moon"
toggle.name = "Switch to system preference"
```

### Custom Colors via CSS

Set `primary = "custom"` then define CSS variables:

```css
/* docs/stylesheets/extra.css */
:root > * {
  --md-primary-fg-color:        #EE0F0F;
  --md-primary-fg-color--light: #ECB7B7;
  --md-primary-fg-color--dark:  #90030C;
}
```

### Custom Color Scheme

```css
[data-md-color-scheme="my-scheme"] {
  --md-primary-fg-color: #EE0F0F;
  /* ... */
}

/* Tune dark scheme hue */
[data-md-color-scheme="slate"] {
  --md-hue: 210;  /* 0-360 */
}
```

## Fonts

```toml
[project.theme]
font.text = "Inter"            # Body text (any Google Font)
font.code = "JetBrains Mono"   # Code blocks (any Google Font)
# font = false                 # Disable Google Fonts, use system fonts
```

Custom fonts via CSS:
```css
:root {
  --md-text-font: "My Custom Font";
  --md-code-font: "My Mono Font";
}
```

## Logo & Icons

```toml
[project.theme]
logo = "images/logo.png"            # Image file in docs/
favicon = "images/favicon.png"

[project.theme.icon]
logo = "lucide/smile"               # Or use a bundled icon
repo = "fontawesome/brands/github"  # Repository icon
edit = "material/pencil"            # Edit page button
view = "material/eye"               # View source button
previous = "fontawesome/solid/angle-left"
next = "fontawesome/solid/angle-right"

[project.extra]
homepage = "https://example.com"    # Override logo link target
```

### Bundled Icon Sets

- Lucide, Material Design, FontAwesome, Octicons, Simple Icons
- Over 10,000 icons available

### Adding Custom Icons

Place SVGs in `overrides/.icons/<set-name>/`:
```toml
[project.theme]
custom_dir = "overrides"

[project.markdown_extensions.pymdownx.emoji]
emoji_index = "zensical.extensions.emoji.twemoji"
emoji_generator = "zensical.extensions.emoji.to_svg"
options.custom_icons = ["overrides/.icons"]
```

## Language

```toml
[project.theme]
language = "en"       # 60+ languages supported
direction = "ltr"     # or "rtl"
```

### Language Selector

```toml
[project.extra]
alternate = [
  { name = "English", link = "/en/", lang = "en" },
  { name = "Deutsch", link = "/de/", lang = "de" }
]
```

## Repository Integration

```toml
[project]
repo_url = "https://github.com/org/repo"
repo_name = "org/repo"
edit_uri = "edit/main/docs/"

[project.theme]
features = [
  "content.action.edit",   # Edit this page button
  "content.action.view"    # View source button
]
```

## Footer

```toml
[project]
copyright = "Copyright &copy; 2025 My Company"

[project.theme]
features = ["navigation.footer"]

[[project.extra.social]]
icon = "fontawesome/brands/github"
link = "https://github.com/org"

[[project.extra.social]]
icon = "fontawesome/brands/x-twitter"
link = "https://x.com/handle"
name = "Company on X"

[project.extra]
generator = false    # Remove "Made with Zensical" (consider keeping it!)
```

## Search

Built-in, enabled by default. English only currently.

```toml
[project.theme]
features = ["search.highlight"]   # Highlight search terms on result pages
```

## Header

```toml
[project.theme]
features = [
  "header.autohide",     # Hide header on scroll down
  "announce.dismiss"     # Dismissable announcement bar
]
```

Announcement bar via template override:
```html
<!-- overrides/main.html -->
{% extends "base.html" %}
{% block announce %}
  Your announcement here!
{% endblock %}
```

## Analytics

```toml
[project.extra.analytics]
provider = "google"
property = "G-XXXXXXXXXX"

[project.extra.analytics.feedback]
title = "Was this page helpful?"

[[project.extra.analytics.feedback.ratings]]
icon = "material/emoticon-happy-outline"
name = "This page was helpful"
data = 1
note = "Thanks for your feedback!"

[[project.extra.analytics.feedback.ratings]]
icon = "material/emoticon-sad-outline"
name = "This page could be improved"
data = 0
note = "Thanks for your feedback!"
```

## Data Privacy / Cookie Consent

```toml
[project.extra.consent]
title = "Cookie consent"
description = "We use cookies to measure our docs effectiveness."
actions = ["accept", "manage"]

[project.extra.consent.cookies]
analytics = "Google Analytics"
custom = "Custom cookie"
```

Change cookie settings link in footer:
```toml
[project]
copyright = """
  Copyright &copy; 2025 –
  <a href="#__consent">Change cookie settings</a>
"""
```

## Tags

Tags work by default. Add to pages via front matter:
```yaml
---
tags:
  - Setup
  - Getting started
---
```

Tag icons:
```toml
[project.extra.tags]
HTML5 = "html"

[project.theme.icon.tag]
default = "lucide/hash"
html = "fontawesome/brands/html5"
```

## Offline Usage

```toml
[project.plugins.offline]
# enabled = false  # To disable
```

Limitations: disable instant navigation, analytics, repo info, comments.

## Custom CSS & JavaScript

```toml
[project]
extra_css = ["stylesheets/extra.css"]
extra_javascript = ["javascripts/extra.js"]
```

JavaScript modules:
```toml
[[project.extra_javascript]]
path = "javascripts/extra.js"
type = "module"
```

Async scripts:
```toml
[[project.extra_javascript]]
path = "javascripts/extra.js"
async = true
```

Important: use `document$` observable for instant navigation compatibility:
```javascript
document$.subscribe(function() {
  console.log("Initialize third-party libraries here")
})
```

## Template Overrides

```toml
[project.theme]
custom_dir = "overrides"
```

### Override Blocks (recommended)

```html
<!-- overrides/main.html -->
{% extends "base.html" %}

{% block htmltitle %}
  <title>Custom Title</title>
{% endblock %}
```

Available blocks: `analytics`, `announce`, `config`, `container`, `content`,
`extrahead`, `fonts`, `footer`, `header`, `hero`, `htmltitle`, `libs`,
`outdated`, `scripts`, `site_meta`, `site_nav`, `styles`, `tabs`.

### Override Partials

Place files in `overrides/partials/` matching the theme's partial structure.

### Custom Templates (per page)

```yaml
---
template: my_template.html
---
```

### Custom 404 Page

Place `404.html` in the overrides directory.

## Markdown Extensions (Default Configuration)

Zensical has sensible defaults. If you need to customize, here is the full
default expansion you can use as a starting point:

```toml
[project.markdown_extensions.abbr]
[project.markdown_extensions.admonition]
[project.markdown_extensions.attr_list]
[project.markdown_extensions.def_list]
[project.markdown_extensions.footnotes]
[project.markdown_extensions.md_in_html]
[project.markdown_extensions.toc]
permalink = true
[project.markdown_extensions.pymdownx.arithmatex]
generic = true
[project.markdown_extensions.pymdownx.betterem]
smart_enable = "all"
[project.markdown_extensions.pymdownx.caret]
[project.markdown_extensions.pymdownx.details]
[project.markdown_extensions.pymdownx.emoji]
emoji_generator = "zensical.extensions.emoji.to_svg"
emoji_index = "zensical.extensions.emoji.twemoji"
[project.markdown_extensions.pymdownx.highlight]
[project.markdown_extensions.pymdownx.inlinehilite]
[project.markdown_extensions.pymdownx.keys]
[project.markdown_extensions.pymdownx.mark]
[project.markdown_extensions.pymdownx.smartsymbols]
[project.markdown_extensions.pymdownx.superfences]
[project.markdown_extensions.pymdownx.tabbed]
alternate_style = true
[project.markdown_extensions.pymdownx.tasklist]
custom_checkbox = true
[project.markdown_extensions.pymdownx.tilde]
```

To reset to MkDocs defaults (no extensions):
```toml
[project]
markdown_extensions = {}
```

## Deployment

### GitHub Pages (GitHub Actions)

```yaml
# .github/workflows/docs.yml
name: Documentation
on:
  push:
    branches: [master, main]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/configure-pages@v5
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v5
        with:
          python-version: 3.x
      - run: pip install zensical
      - run: zensical build --clean
      - uses: actions/upload-pages-artifact@v4
        with:
          path: site
      - uses: actions/deploy-pages@v4
        id: deployment
```

Site appears at `<username>.github.io/<repository>`.

### GitLab Pages

```yaml
# .gitlab-ci.yml
pages:
  stage: deploy
  image: python:latest
  script:
    - pip install zensical
    - zensical build --clean
  pages:
    publish: public
  rules:
    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'
```

**Important:** Set `site_dir = "public"` for GitLab Pages.

Site appears at `<username>.gitlab.io/<repository>`.

## Content Area Width

```css
/* docs/stylesheets/extra.css */
.md-grid {
  max-width: 1440px;
  /* Or: max-width: initial; for full width */
}
```

## mkdocstrings (API docs)

```bash
pip install mkdocstrings-python
```

```toml
[project.plugins.mkdocstrings.handlers.python]
paths = ["src"]
inventories = ["https://docs.python.org/3/objects.inv"]

[project.plugins.mkdocstrings.handlers.python.options]
docstring_style = "google"
inherited_members = true
show_source = false
```

## Comment System (Giscus example)

Override `partials/comments.html` with the Giscus script, then enable per page:
```yaml
---
comments: true
---
```

## CLI Reference

| Command | Purpose |
|---------|---------|
| `zensical new <dir>` | Create new project |
| `zensical serve` | Preview with live reload |
| `zensical serve -o` | Preview and open browser |
| `zensical serve -a localhost:3000` | Custom address |
| `zensical build` | Build static site |
| `zensical build --clean` | Build with cache cleaning |
| `zensical build -f path/to/config` | Use specific config file |