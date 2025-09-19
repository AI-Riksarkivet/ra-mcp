import re
from bs4 import BeautifulSoup
import html2text
from pathlib import Path
import os

def fix_swedish_encoding(text):
    """Fix common Swedish character encoding issues"""
    replacements = {
        'Ã¶': 'ö',
        'Ã¤': 'ä',
        'Ã¥': 'å',
        'Ã–': 'Ö',
        'Ã„': 'Ä',
        'Ã…': 'Å',
        'Ã©': 'é',
        'Ã¨': 'è',
        'Ã¼': 'ü',
        'Ã¸': 'ø',
        'Ã˜': 'Ø',
        'â€™': "'",
        'â€"': '–',
        'â€"': '—',
        'â€œ': '"',
        'â€': '"',
        'â€¦': '…',
        'Â ': ' ',  # non-breaking space
    }

    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result

def html_to_markdown(html_content, filename):
    """Convert HTML content to Markdown with proper formatting"""

    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script and style elements
    for element in soup(['script', 'style', 'meta', 'link']):
        element.decompose()

    # Initialize html2text converter
    h = html2text.HTML2Text()
    h.body_width = 0  # Don't wrap lines
    h.ignore_links = False
    h.ignore_images = False
    h.unicode_snob = True

    # Get the body content if it exists, otherwise use all content
    body = soup.find('body')
    if body:
        content = str(body)
    else:
        content = str(soup)

    # Convert to markdown
    markdown = h.handle(content)

    # Fix Swedish encoding issues
    markdown = fix_swedish_encoding(markdown)

    # Clean up excessive blank lines
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)

    # Add metadata header
    title = soup.find('title')
    if title:
        title_text = fix_swedish_encoding(title.get_text())
    else:
        title_text = filename.replace('.htm', '').replace('_', ' ')

    # Extract meta information
    meta_info = []
    author = soup.find('meta', {'name': 'Author'})
    if author:
        meta_info.append(f"author: {fix_swedish_encoding(author.get('content', ''))}")

    description = soup.find('meta', {'name': 'Description'})
    if description:
        meta_info.append(f"description: {fix_swedish_encoding(description.get('content', ''))}")

    # Build the final markdown with frontmatter
    frontmatter = f"""---
title: {title_text}
{chr(10).join(meta_info)}
---

"""

    return frontmatter + markdown

def convert_all_files():
    """Find and convert all HTM files in riksarkivet_data/html directory"""

    # Define paths
    html_dir = Path("riksarkivet_data/html")
    markdown_dir = Path("riksarkivet_data/markdown")

    # Create markdown directory if it doesn't exist
    markdown_dir.mkdir(parents=True, exist_ok=True)

    # Find all .htm files
    htm_files = list(html_dir.glob("*.htm"))

    if not htm_files:
        print(f"No .htm files found in {html_dir}")
        return

    print(f"Found {len(htm_files)} HTM files to convert")
    print("-" * 50)

    # Convert each file
    successful = 0
    failed = 0

    for filepath in htm_files:
        try:
            # Read the HTML file
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()

            # Convert to markdown
            filename = filepath.name
            markdown_content = html_to_markdown(html_content, filename)

            # Save as .md file in the markdown directory
            output_path = markdown_dir / filepath.with_suffix('.md').name
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print(f"✓ Converted: {filename} -> {output_path.name}")
            successful += 1

        except Exception as e:
            print(f"✗ Failed to convert {filepath.name}: {str(e)}")
            failed += 1

    print("-" * 50)
    print(f"Conversion complete: {successful} successful, {failed} failed")
    print(f"Markdown files saved in: {markdown_dir}")

if __name__ == "__main__":
    # First check if beautifulsoup4 and html2text are installed
    try:
        import bs4
        import html2text
    except ImportError:
        print("Required libraries not installed. Please run:")
        print("pip install beautifulsoup4 html2text")
        exit(1)

    # Run the conversion
    convert_all_files()


####################################################################################################################################
####################################################################################################################################
####################################################################################################################################





import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import os
import json

class RiksarkivetScraper:
    def __init__(self, base_url="https://forvaltningshistorik.riksarkivet.se/"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.visited_urls = set()
        self.all_content = {}
        self.to_visit = set()

    def is_valid_url(self, url):
        """Check if URL belongs to the target domain"""
        parsed = urlparse(url)
        base_parsed = urlparse(self.base_url)

        # Only scrape URLs from the same domain
        if parsed.netloc and parsed.netloc != base_parsed.netloc:
            return False

        # Skip non-HTML files (images, PDFs, etc.)
        if url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.xls')):
            return False

        return True

    def extract_links(self, soup, current_url):
        """Extract all valid links from a page"""
        links = set()

        for tag in soup.find_all(['a', 'link']):
            href = tag.get('href')
            if href:
                # Skip anchors and mailto links
                if href.startswith('#') or href.startswith('mailto:'):
                    continue

                # Convert relative URLs to absolute
                absolute_url = urljoin(current_url, href)

                if self.is_valid_url(absolute_url):
                    links.add(absolute_url)

        return links

    def scrape_page(self, url):
        """Scrape a single page and extract its content and links"""
        if url in self.visited_urls:
            return None

        try:
            print(f"Scraping: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # Handle encoding
            if response.apparent_encoding:
                response.encoding = response.apparent_encoding
            else:
                response.encoding = 'iso-8859-1'

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract content
            title = soup.title.string if soup.title else "No title"

            # Get text content
            text_content = soup.get_text(separator='\n', strip=True)

            # Get raw HTML
            html_content = response.text

            # Store the content
            self.all_content[url] = {
                'title': title,
                'text': text_content,
                'html': html_content,
                'links_found': []
            }

            # Mark as visited
            self.visited_urls.add(url)

            # Find all links on this page
            new_links = self.extract_links(soup, url)
            self.all_content[url]['links_found'] = list(new_links)

            # Add new links to the queue
            for link in new_links:
                if link not in self.visited_urls:
                    self.to_visit.add(link)

            return new_links

        except Exception as e:
            print(f"  Error scraping {url}: {e}")
            self.visited_urls.add(url)  # Mark as visited even if failed
            return None

    def scrape_all(self, start_url=None):
        """Recursively scrape all pages starting from the index"""
        if not start_url:
            start_url = urljoin(self.base_url, "Index.htm")

        # Initialize with start URL
        self.to_visit.add(start_url)

        # Keep scraping until we've visited all discovered URLs
        while self.to_visit:
            # Get next URL to visit
            current_url = self.to_visit.pop()

            if current_url not in self.visited_urls:
                # Scrape the page (this will add new URLs to self.to_visit)
                self.scrape_page(current_url)

                # Be respectful - add delay
                time.sleep(0.5)

                # Progress update
                print(f"  Progress: Visited {len(self.visited_urls)} pages, "
                      f"{len(self.to_visit)} remaining in queue")

        print(f"\nScraping complete! Total pages scraped: {len(self.all_content)}")
        return self.all_content

    def save_to_files(self, output_dir="riksarkivet_data"):
        """Save all scraped content to files"""
        os.makedirs(output_dir, exist_ok=True)

        # Save individual HTML files
        html_dir = os.path.join(output_dir, "html")
        os.makedirs(html_dir, exist_ok=True)

        # Save individual text files
        text_dir = os.path.join(output_dir, "text")
        os.makedirs(text_dir, exist_ok=True)

        # Create index of all pages
        index_data = {}

        for url, content in self.all_content.items():
            # Create filename from URL
            parsed = urlparse(url)
            filename = parsed.path.strip('/').replace('/', '_')
            if not filename:
                filename = "index"

            # Save HTML
            html_path = os.path.join(html_dir, filename)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(content['html'])

            # Save text
            text_path = os.path.join(text_dir, filename.replace('.htm', '.txt'))
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(f"Title: {content['title']}\n")
                f.write(f"URL: {url}\n")
                f.write(f"{'='*50}\n\n")
                f.write(content['text'])

            # Add to index
            index_data[url] = {
                'title': content['title'],
                'html_file': html_path,
                'text_file': text_path,
                'links': content['links_found']
            }

        # Save index as JSON
        with open(os.path.join(output_dir, 'index.json'), 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        # Save all text in one file
        with open(os.path.join(output_dir, 'all_content.txt'), 'w', encoding='utf-8') as f:
            for url, content in self.all_content.items():
                f.write(f"\n{'='*80}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Title: {content['title']}\n")
                f.write(f"{'='*80}\n")
                f.write(content['text'])
                f.write(f"\n\n")

        print(f"All content saved to {output_dir}/")
        print(f"  - HTML files: {html_dir}/")
        print(f"  - Text files: {text_dir}/")
        print(f"  - Complete index: {output_dir}/index.json")
        print(f"  - All text: {output_dir}/all_content.txt")

# Run the scraper
if __name__ == "__main__":
    scraper = RiksarkivetScraper()

    # Scrape everything
    all_content = scraper.scrape_all()

    # Save to files
    scraper.save_to_files()

    # Print summary
    print(f"\nSummary:")
    print(f"Total pages scraped: {len(all_content)}")
    print(f"Total links discovered: {sum(len(c['links_found']) for c in all_content.values())}")

