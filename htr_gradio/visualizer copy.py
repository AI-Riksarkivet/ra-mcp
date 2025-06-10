import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os
from typing import Optional, Tuple, List
import math


def htrflow_visualizer(image_path: str, htr_document_path: str) -> Optional[str]:
    """
    Visualize HTR results by overlaying text regions and polygons on the original image.

    Args:
        image_path: Path to the original image
        htr_document_path: Path to the ALTO or PAGE XML file

    Returns:
        str: Path to the visualization image, or None if failed
    """
    try:
        if not image_path or not htr_document_path:
            return None

        # Load the original image
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)

        # Parse the XML document
        tree = ET.parse(htr_document_path)
        root = tree.getroot()

        print(f"Root tag: {root.tag}")
        print(f"Root attributes: {root.attrib}")

        # Determine if it's PAGE or ALTO XML based on namespace/structure
        if "alto" in root.tag.lower() or root.find(".//TextBlock") is not None:
            print("Detected ALTO XML format")
            # Handle ALTO XML format
            _visualize_alto_xml(draw, root, image.size)
        elif "PAGE" in root.tag or "PcGts" in root.tag:
            print("Detected PAGE XML format")
            # Handle PAGE XML format
            _visualize_page_xml(draw, root, image.size)
        else:
            print("Auto-detecting format...")
            # Try to auto-detect based on content
            if root.find(".//*[@points]") is not None:
                print("Found points attribute, using PAGE format")
                _visualize_page_xml(draw, root, image.size)
            else:
                print("Defaulting to ALTO format")
                _visualize_alto_xml(draw, root, image.size)

        # Save the visualization
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "htr_visualization.png")
        image.save(output_path)

        return output_path

    except Exception as e:
        print(f"Visualization failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def _parse_points(points_str: str) -> List[Tuple[int, int]]:
    """Parse points string from XML format: 'x1,y1 x2,y2 x3,y3 ...'"""
    if not points_str:
        return []

    points = []
    coords = points_str.strip().split()
    for coord in coords:
        if "," in coord:
            try:
                x, y = coord.split(",")
                points.append((int(float(x)), int(float(y))))
            except ValueError:
                continue
    return points


def _calculate_polygon_area(points: List[Tuple[int, int]]) -> float:
    """Calculate the area of a polygon using the shoelace formula"""
    if len(points) < 3:
        return 0

    area = 0
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return abs(area) / 2


def _get_dynamic_font_size(
    polygons: List[List[Tuple[int, int]]], image_size: Tuple[int, int]
) -> int:
    """Calculate appropriate font size based on average polygon dimensions"""
    if not polygons:
        return 16

    total_area = 0
    valid_polygons = 0

    for points in polygons:
        if len(points) >= 3:
            area = _calculate_polygon_area(points)
            if area > 0:
                total_area += area
                valid_polygons += 1

    if valid_polygons == 0:
        return 16

    avg_area = total_area / valid_polygons

    # Calculate font size as a fraction of the square root of average area
    # This gives reasonable scaling
    font_size = max(8, min(72, int(math.sqrt(avg_area) * 0.15)))

    print(
        f"Calculated font size: {font_size} (from {valid_polygons} polygons, avg area: {avg_area:.2f})"
    )
    return font_size


def _get_font(size: int) -> Optional[ImageFont.FreeTypeFont]:
    """Get font with specified size, with fallback options"""
    font_paths = [
        "arial.ttf",
        "Arial.ttf",
        "/System/Library/Fonts/Arial.ttf",  # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "C:/Windows/Fonts/arial.ttf",  # Windows
    ]

    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            continue

    try:
        return ImageFont.load_default()
    except:
        return None


def _visualize_page_xml(
    draw: ImageDraw.Draw, root: ET.Element, image_size: Tuple[int, int]
):
    """Visualize PAGE XML format with polygon coordinates"""
    # Find all TextLine elements with coordinates and text
    namespaces = {
        "ns": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
    }

    # Try with and without namespace
    text_lines = root.findall(".//ns:TextLine", namespaces)
    if not text_lines:
        text_lines = root.findall(".//TextLine")

    print(f"Found {len(text_lines)} text lines")

    # First pass: collect all polygons for font sizing
    all_polygons = []
    line_data = []

    for text_line in text_lines:
        # Get coordinates
        coords_elem = text_line.find(".//ns:Coords", namespaces)
        if coords_elem is None:
            coords_elem = text_line.find(".//Coords")

        if coords_elem is not None:
            points_str = coords_elem.get("points", "")
            points = _parse_points(points_str)

            if len(points) >= 3:
                all_polygons.append(points)

                # Get text content and confidence
                text_equiv = text_line.find(".//ns:TextEquiv/ns:Unicode", namespaces)
                if text_equiv is None:
                    text_equiv = text_line.find(".//TextEquiv/Unicode")

                text = (
                    text_equiv.text.strip()
                    if text_equiv is not None and text_equiv.text
                    else ""
                )

                # Get confidence score
                confidence = None
                text_equiv_parent = text_line.find(".//ns:TextEquiv", namespaces)
                if text_equiv_parent is None:
                    text_equiv_parent = text_line.find(".//TextEquiv")

                if text_equiv_parent is not None:
                    conf_attr = text_equiv_parent.get("conf")
                    if conf_attr:
                        try:
                            confidence = float(conf_attr)
                        except ValueError:
                            pass

                # Format text with confidence if available
                display_text = text
                if confidence is not None:
                    display_text = f"{text} ({confidence:.3f})"

                line_data.append((points, display_text))

    # Calculate dynamic font size
    font_size = _get_dynamic_font_size(all_polygons, image_size)
    font = _get_font(font_size)

    # Second pass: draw polygons and text
    for i, (points, text) in enumerate(line_data):
        # Draw polygon outline with alternating colors for visibility
        color = "red" if i % 2 == 0 else "blue"
        draw.polygon(points, outline=color, width=2, fill=None)

        if text:
            # Calculate polygon centroid for text placement
            centroid_x = sum(p[0] for p in points) // len(points)
            centroid_y = sum(p[1] for p in points) // len(points)

            # Draw text with semi-transparent background for visibility
            if font:
                bbox = draw.textbbox((centroid_x, centroid_y), text, font=font)
                # Add padding to bbox
                bbox = (bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2)
                draw.rectangle(bbox, fill=(255, 255, 255, 200), outline="black")
                draw.text((centroid_x, centroid_y), text, fill="black", font=font)
            else:
                draw.text((centroid_x, centroid_y), text, fill=color)


def _visualize_alto_xml(
    draw: ImageDraw.Draw, root: ET.Element, image_size: Tuple[int, int]
):
    """Visualize ALTO XML format with polygon shapes"""

    print("Starting ALTO XML visualization...")

    # Collect all polygons for font size calculation
    all_polygons = []
    elements_with_polygons = []

    # First, look for TextBlock polygons (larger regions)
    text_blocks = root.findall(".//TextBlock")
    print(f"Found {len(text_blocks)} TextBlock elements")

    for text_block in text_blocks:
        text_block_id = text_block.get("ID", "")
        print(f"Processing TextBlock: {text_block_id}")

        # Look for Shape/Polygon within the TextBlock
        shape = text_block.find("Shape")
        if shape is not None:
            polygon = shape.find("Polygon")
            if polygon is not None:
                points_str = polygon.get("POINTS", "")
                print(f"Found TextBlock polygon: {points_str[:50]}...")
                points = _parse_points(points_str)

                if len(points) >= 3:
                    all_polygons.append(points)
                    elements_with_polygons.append(
                        ("TextBlock", points, f"TextBlock {text_block_id}")
                    )

    # Now look for TextLine elements (individual text lines)
    text_lines = root.findall(".//TextLine")
    print(f"Found {len(text_lines)} TextLine elements")

    for text_line in text_lines:
        text_line_id = text_line.get("ID", "")
        print(f"Processing TextLine: {text_line_id}")

        # Look for Shape/Polygon within the TextLine
        shape = text_line.find("Shape")
        if shape is not None:
            polygon = shape.find("Polygon")
            if polygon is not None:
                points_str = polygon.get("POINTS", "")
                print(f"Found TextLine polygon: {points_str[:50]}...")
                points = _parse_points(points_str)

                if len(points) >= 3:
                    all_polygons.append(points)

                    # Get text content from String element within TextLine
                    string_elem = text_line.find("String")
                    text_content = ""
                    confidence = None

                    if string_elem is not None:
                        text_content = string_elem.get("CONTENT", "")
                        wc_attr = string_elem.get("WC")
                        if wc_attr:
                            try:
                                confidence = float(wc_attr)
                            except ValueError:
                                pass

                    # Format text with confidence if available
                    display_text = text_content
                    if confidence is not None:
                        display_text = f"{text_content} ({confidence:.3f})"

                    elements_with_polygons.append(("TextLine", points, display_text))
                    print(f"Added TextLine polygon with text: {display_text}")
                else:
                    print(
                        f"Invalid polygon (less than 3 points) in TextLine {text_line_id}"
                    )
            else:
                print(f"No Polygon found in Shape for TextLine {text_line_id}")
        else:
            print(f"No Shape found in TextLine {text_line_id}")

    print(f"Total polygons found: {len(all_polygons)}")

    if not all_polygons:
        print("No polygons found! Checking for alternative structures...")
        # Alternative: look for elements with HPOS/VPOS coordinates as rectangles
        for elem_type in ["String", "Word", "TextLine"]:
            elements = root.findall(f".//{elem_type}")
            for element in elements:
                hpos = element.get("HPOS")
                vpos = element.get("VPOS")
                width = element.get("WIDTH")
                height = element.get("HEIGHT")

                if all([hpos, vpos, width, height]):
                    try:
                        x, y, w, h = int(hpos), int(vpos), int(width), int(height)
                        # Create rectangle as polygon
                        points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
                        all_polygons.append(points)

                        text_content = element.get("CONTENT", "")
                        confidence = None
                        wc_attr = element.get("WC")
                        if wc_attr:
                            try:
                                confidence = float(wc_attr)
                            except ValueError:
                                pass

                        # Format text with confidence if available
                        display_text = text_content
                        if confidence is not None:
                            display_text = f"{text_content} ({confidence:.3f})"

                        elements_with_polygons.append((elem_type, points, display_text))
                        print(
                            f"Created rectangle polygon for {elem_type}: {x},{y} {w}x{h}"
                        )
                    except ValueError:
                        continue

    # Calculate dynamic font size
    font_size = _get_dynamic_font_size(all_polygons, image_size)
    font = _get_font(font_size)

    # Draw all polygons
    color_map = {
        "TextBlock": ["green", "purple"],
        "TextLine": ["red", "blue"],
        "String": ["orange", "cyan"],
        "Word": ["magenta", "yellow"],
    }

    for i, (elem_type, points, text_content) in enumerate(elements_with_polygons):
        colors = color_map.get(elem_type, ["black", "gray"])
        color = colors[i % 2]

        # Different line widths for different element types
        width_val = (
            3 if elem_type == "TextBlock" else 2 if elem_type == "TextLine" else 1
        )

        # Draw polygon outline
        draw.polygon(points, outline=color, width=width_val, fill=None)

        if (
            text_content and elem_type == "TextLine"
        ):  # Only draw text for TextLines, not TextBlocks
            # Calculate polygon centroid for text placement
            centroid_x = sum(p[0] for p in points) // len(points)
            centroid_y = sum(p[1] for p in points) // len(points)

            # Draw text with background
            if font:
                bbox = draw.textbbox((centroid_x, centroid_y), text_content, font=font)
                bbox = (bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2)
                draw.rectangle(bbox, fill=(255, 255, 255, 200), outline="black")
                draw.text(
                    (centroid_x, centroid_y), text_content, fill="black", font=font
                )
            else:
                draw.text((centroid_x, centroid_y), text_content, fill=color)
