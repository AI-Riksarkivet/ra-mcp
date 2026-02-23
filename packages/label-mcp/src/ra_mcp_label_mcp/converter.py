import json
import logging
import uuid
import xml.etree.ElementTree as ET


logger = logging.getLogger("ra_mcp.label.converter")

_NS_ALTO = {"a": "http://www.loc.gov/standards/alto/ns-v4#"}

_BASELINE_ASCENT = 40
_BASELINE_DESCENT = 15


def _int(value: str | None, default: int = 0) -> int:
    try:
        return int(value) if value else default
    except ValueError:
        return default


def _polygon_from_baseline(baseline: str, ascent: int = _BASELINE_ASCENT, descent: int = _BASELINE_DESCENT) -> str:
    """Create a polygon strip from a BASELINE attribute."""
    try:
        points = [(int(x), int(y)) for x, y in (p.split(",") for p in baseline.split())]
        if len(points) < 2:
            return ""
        top = [f"{x},{max(0, y - ascent)}" for x, y in points]
        bottom = [f"{x},{y + descent}" for x, y in reversed(points)]
        return " ".join(top + bottom)
    except (ValueError, IndexError):
        return ""


def _parse_points(points_str: str) -> list[tuple[int, int]]:
    """Parse space-separated 'x,y' pairs into a list of (x, y) tuples."""
    points: list[tuple[int, int]] = []
    for pair in points_str.strip().split():
        x, y = pair.split(",")
        points.append((int(x), int(y)))
    return points


def parse_alto(alto_xml: str) -> dict:
    """Parse ALTO v4 XML string into an intermediate dict.

    Returns dict with keys: filename, page_width, page_height, textlines.
    Each textline has: points (list of (x,y) tuples), text, id.
    """
    root = ET.fromstring(alto_xml)

    # Fall back to no-namespace queries if the document lacks xmlns
    ns = _NS_ALTO if root.tag.startswith("{") else {}
    prefix = "a:" if ns else ""

    page = root.find(f".//{prefix}Page", ns)
    if page is None:
        raise ValueError("No <Page> element found in ALTO XML")

    page_width = _int(page.get("WIDTH"))
    page_height = _int(page.get("HEIGHT"))

    filename_el = root.find(f".//{prefix}fileName", ns)
    filename = filename_el.text if filename_el is not None and filename_el.text else "unknown"

    textlines: list[dict] = []
    tag = f"{{{_NS_ALTO['a']}}}TextLine" if ns else "TextLine"
    for tl in root.iter(tag):
        # Polygon fallback chain: Shape/Polygon → BASELINE → bbox
        polygon_el = tl.find(f"{prefix}Shape/{prefix}Polygon", ns)
        points_str = polygon_el.get("POINTS", "") if polygon_el is not None else ""

        if not points_str:
            baseline = tl.get("BASELINE", "")
            if baseline:
                points_str = _polygon_from_baseline(baseline)
            else:
                h, v, w, ht = _int(tl.get("HPOS")), _int(tl.get("VPOS")), _int(tl.get("WIDTH")), _int(tl.get("HEIGHT"))
                if w and ht:
                    points_str = f"{h},{v} {h + w},{v} {h + w},{v + ht} {h},{v + ht}"

        if not points_str:
            continue

        points = _parse_points(points_str)

        strings = tl.findall(f"{prefix}String", ns)
        words = [s.get("CONTENT", "") for s in strings]
        text = " ".join(w for w in words if w)

        textlines.append(
            {
                "points": points,
                "text": text,
                "id": tl.get("ID", ""),
            }
        )

    logger.info(f"Parsed ALTO: {filename}, {page_width}x{page_height}, {len(textlines)} textlines")
    return {
        "filename": filename,
        "page_width": page_width,
        "page_height": page_height,
        "textlines": textlines,
    }


def to_label_studio_task(parsed: dict, image_url: str | None = None) -> dict:
    """Convert parsed ALTO data into a Label Studio task dict.

    Args:
        parsed: Output from parse_alto().
        image_url: Full URL to the page image. Falls back to local-files path.

    Returns:
        Label Studio task dict with data and predictions.
    """
    if image_url is None:
        image_url = f"/data/local-files/?d={parsed['filename']}"

    pw = parsed["page_width"]
    ph = parsed["page_height"]
    results: list[dict] = []

    for tl in parsed["textlines"]:
        region_id = str(uuid.uuid4())[:8]

        vertices: list[dict] = []
        for x, y in tl["points"]:
            point_id = f"pt-{uuid.uuid4().hex[:6]}"
            vertices.append(
                {
                    "id": point_id,
                    "x": x / pw * 100,
                    "y": y / ph * 100,
                    "prevPointId": vertices[-1]["id"] if vertices else None,
                    "isBezier": False,
                }
            )

        # VectorLabels region
        results.append(
            {
                "id": region_id,
                "type": "vectorlabels",
                "from_name": "label",
                "to_name": "image",
                "original_width": pw,
                "original_height": ph,
                "image_rotation": 0,
                "value": {
                    "vertices": vertices,
                    "closed": True,
                    "vectorlabels": ["Textlines"],
                },
            }
        )

        # Transcription region (linked to same region_id)
        results.append(
            {
                "id": region_id,
                "type": "textarea",
                "from_name": "transcription",
                "to_name": "image",
                "original_width": pw,
                "original_height": ph,
                "image_rotation": 0,
                "value": {
                    "vertices": vertices,
                    "closed": True,
                    "text": [tl["text"]],
                },
            }
        )

    return {
        "data": {"ocr": image_url},
        "predictions": [{"result": results}],
    }


def convert_alto_to_tasks(
    alto_xmls: list[str],
    image_base_url: str | None = None,
) -> list[dict]:
    """Convert multiple ALTO XML strings to Label Studio tasks.

    Args:
        alto_xmls: List of ALTO XML strings.
        image_base_url: Base URL prefix for images (appended with filename).

    Returns:
        List of Label Studio task dicts.
    """
    tasks: list[dict] = []
    for alto_xml in alto_xmls:
        parsed = parse_alto(alto_xml)
        if image_base_url:
            image_url = f"{image_base_url.rstrip('/')}/{parsed['filename']}"
        else:
            image_url = None
        tasks.append(to_label_studio_task(parsed, image_url=image_url))

    logger.info(f"Converted {len(tasks)} ALTO file(s) to Label Studio tasks")
    return tasks


def tasks_to_json(tasks: list[dict]) -> str:
    """Serialize Label Studio tasks to JSON string."""
    return json.dumps(tasks, indent=2, ensure_ascii=False)
