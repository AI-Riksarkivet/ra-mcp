import logging
import xml.etree.ElementTree as ET

from src.models import TextLayer, TextLine

logger = logging.getLogger(__name__)

_DEFAULT_PAGE_WIDTH = 6192
_DEFAULT_PAGE_HEIGHT = 5432

_NS_ALTO = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}
_NS_PAGE = {"p": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"}


def _build_text_layer(
    lines: list[TextLine],
    page_width: int,
    page_height: int,
    format_label: str,
) -> TextLayer:
    """Filter lines with both polygon and transcription, log skips, return TextLayer."""
    valid: list[TextLine] = []
    transcription_lines: list[str] = []
    skipped_no_polygon = 0
    skipped_no_transcription = 0

    for line in lines:
        if not line.polygon:
            skipped_no_polygon += 1
        if not line.transcription:
            skipped_no_transcription += 1
        if line.polygon and line.transcription:
            valid.append(line)
            transcription_lines.append(line.transcription)

    logger.info("%s parsed: %d text lines, page %dx%d", format_label, len(valid), page_width, page_height)
    if skipped_no_polygon:
        logger.warning("Skipped %d lines with no polygon", skipped_no_polygon)
    if skipped_no_transcription:
        logger.warning("Skipped %d lines with no transcription", skipped_no_transcription)

    return TextLayer(
        text_lines=valid,
        page_width=page_width,
        page_height=page_height,
        full_text="\n".join(transcription_lines),
    )


def _bbox_from_polygon(polygon: str) -> tuple[int, int, int, int]:
    """Compute (hpos, vpos, width, height) from space-separated x,y points."""
    try:
        points = [tuple(int(v) for v in p.split(",")) for p in polygon.split()]
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
    except (ValueError, IndexError):
        return 0, 0, 0, 0


def _int(value: str | None, default: int = 0) -> int:
    try:
        return int(value) if value else default
    except ValueError:
        return default


def _float(value: str | None) -> float | None:
    try:
        return float(value) if value else None
    except ValueError:
        return None


def parse_alto_xml(xml_string: str) -> TextLayer:
    """Parse ALTO v4 XML into a TextLayer. Joins word-level Strings per TextLine."""
    root = ET.fromstring(xml_string)

    # Fall back to no-namespace queries if the document lacks xmlns
    ns = _NS_ALTO if root.tag.startswith("{") else {}
    prefix = "a:" if ns else ""

    page_el = root.find(f".//{prefix}Page", ns)
    if page_el is not None:
        page_width = _int(page_el.get("WIDTH"), _DEFAULT_PAGE_WIDTH)
        page_height = _int(page_el.get("HEIGHT"), _DEFAULT_PAGE_HEIGHT)
    else:
        page_width, page_height = _DEFAULT_PAGE_WIDTH, _DEFAULT_PAGE_HEIGHT
        logger.warning("No <Page> element found, using defaults: %dx%d", page_width, page_height)

    lines: list[TextLine] = []
    for tl in root.iter(f"{{{_NS_ALTO['a']}}}" + "TextLine" if ns else "TextLine"):
        polygon_el = tl.find(f"{prefix}Shape/{prefix}Polygon", ns)
        polygon = polygon_el.get("POINTS", "") if polygon_el is not None else ""

        strings = tl.findall(f"{prefix}String", ns)
        words = [s.get("CONTENT", "") for s in strings]
        transcription = " ".join(w for w in words if w)

        confidence: float | None = None
        wc_valid = [v for s in strings if (v := _float(s.get("WC"))) is not None]
        if wc_valid:
            confidence = sum(wc_valid) / len(wc_valid)

        lines.append(TextLine(
            id=tl.get("ID", ""),
            polygon=polygon,
            transcription=transcription,
            hpos=_int(tl.get("HPOS")),
            vpos=_int(tl.get("VPOS")),
            width=_int(tl.get("WIDTH")),
            height=_int(tl.get("HEIGHT")),
            confidence=confidence,
        ))

    return _build_text_layer(lines, page_width, page_height, "ALTO")


def parse_page_xml(xml_string: str) -> TextLayer:
    """Parse PAGE XML (PcGts) into a TextLayer. Computes bounding box from Coords polygon."""
    root = ET.fromstring(xml_string)

    ns = _NS_PAGE if root.tag.startswith("{") else {}
    prefix = "p:" if ns else ""

    page_el = root.find(f".//{prefix}Page", ns)
    if page_el is not None:
        page_width = _int(page_el.get("imageWidth"), _DEFAULT_PAGE_WIDTH)
        page_height = _int(page_el.get("imageHeight"), _DEFAULT_PAGE_HEIGHT)
    else:
        page_width, page_height = _DEFAULT_PAGE_WIDTH, _DEFAULT_PAGE_HEIGHT
        logger.warning("No <Page> element found, using defaults: %dx%d", page_width, page_height)

    lines: list[TextLine] = []
    for tl in root.iter(f"{{{_NS_PAGE['p']}}}" + "TextLine" if ns else "TextLine"):
        coords_el = tl.find(f"{prefix}Coords", ns)
        polygon = coords_el.get("points", "") if coords_el is not None else ""

        te_el = tl.find(f"{prefix}TextEquiv", ns)
        transcription = ""
        confidence: float | None = None
        if te_el is not None:
            unicode_el = te_el.find(f"{prefix}Unicode", ns)
            transcription = (unicode_el.text or "").strip() if unicode_el is not None else ""
            confidence = _float(te_el.get("conf"))

        hpos, vpos, width, height = _bbox_from_polygon(polygon) if polygon else (0, 0, 0, 0)

        lines.append(TextLine(
            id=tl.get("id", ""),
            polygon=polygon,
            transcription=transcription,
            hpos=hpos,
            vpos=vpos,
            width=width,
            height=height,
            confidence=confidence,
        ))

    return _build_text_layer(lines, page_width, page_height, "PAGE XML")


def detect_and_parse(xml_string: str) -> TextLayer:
    """Auto-detect XML format (ALTO vs PAGE) and parse accordingly."""
    if "<PcGts" in xml_string[:500]:
        return parse_page_xml(xml_string)
    return parse_alto_xml(xml_string)
