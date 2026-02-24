"""RA-MCP XML: ALTO and PAGE XML client for Riksarkivet."""

__version__ = "0.3.0"

from .client import ALTOClient
from .models import TextLayer, TextLine
from .parser import detect_and_parse, parse_alto_xml, parse_page_xml


__all__ = ["ALTOClient", "TextLayer", "TextLine", "detect_and_parse", "parse_alto_xml", "parse_page_xml"]
