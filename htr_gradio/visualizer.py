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
        image_path (str): Path to the original document image file
        htr_document_path (str): Path to the HTR XML file (ALTO or PAGE format)

    Returns:
        Optional[str]: Path to the generated visualization image, or None if failed
    """
    try:
        if not image_path or not htr_document_path:
            return None

        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)

        tree = ET.parse(htr_document_path)
        root = tree.getroot()

        if "alto" in root.tag.lower() or root.find(".//TextBlock") is not None:
            _visualize_alto_xml(draw, root, image.size)
        elif "PAGE" in root.tag or "PcGts" in root.tag:
            _visualize_page_xml(draw, root, image.size)
        else:
            if root.find(".//*[@points]") is not None:
                _visualize_page_xml(draw, root, image.size)
            else:
                _visualize_alto_xml(draw, root, image.size)

        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "htr_visualization.png")
        image.save(output_path)

        return output_path

    except Exception:
        return None


def _parse_points(points_str: str) -> List[Tuple[int, int]]:
    if not points_str:
        return []

    points = []
    for coord in points_str.strip().split():
        if "," in coord:
            try:
                x, y = coord.split(",")
                points.append((int(float(x)), int(float(y))))
            except ValueError:
                continue
    return points


def _calculate_polygon_area(points: List[Tuple[int, int]]) -> float:
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
    if not polygons:
        return 16

    total_area = sum(
        _calculate_polygon_area(points) for points in polygons if len(points) >= 3
    )
    valid_polygons = sum(
        1
        for points in polygons
        if len(points) >= 3 and _calculate_polygon_area(points) > 0
    )

    if valid_polygons == 0:
        return 16

    avg_area = total_area / valid_polygons
    return max(8, min(72, int(math.sqrt(avg_area) * 0.15)))


def _get_font(size: int) -> Optional[ImageFont.FreeTypeFont]:
    try:
        return ImageFont.load_default()
    except:
        return None


def _get_namespace(root: ET.Element) -> Optional[str]:
    if "}" in root.tag:
        return root.tag.split("}")[0] + "}"
    return None


def _find_elements_with_namespace(
    root: ET.Element, element_name: str, namespace: Optional[str]
) -> List[ET.Element]:
    elements = root.findall(f".//{element_name}")

    if not elements and namespace:
        elements = root.findall(f".//{namespace}{element_name}")

    if not elements:
        elements = [elem for elem in root.iter() if elem.tag.endswith(element_name)]

    return elements


def _find_child_element(
    parent: ET.Element, element_name: str, namespace: Optional[str]
) -> Optional[ET.Element]:
    element = parent.find(element_name)

    if element is None and namespace:
        element = parent.find(f"{namespace}{element_name}")

    if element is None:
        elements = [child for child in parent if child.tag.endswith(element_name)]
        element = elements[0] if elements else None

    return element


def _extract_text_and_confidence(
    element: ET.Element, namespace: Optional[str], format_type: str
) -> Tuple[str, Optional[float]]:
    text_content = ""
    confidence = None

    if format_type == "alto":
        string_elem = _find_child_element(element, "String", namespace)
        if string_elem is not None:
            text_content = string_elem.get("CONTENT", "")
            wc_attr = string_elem.get("WC")
            if wc_attr:
                try:
                    confidence = float(wc_attr)
                except ValueError:
                    pass

    elif format_type == "page":
        text_equiv = element.find(".//TextEquiv/Unicode")
        if text_equiv is not None and text_equiv.text:
            text_content = text_equiv.text.strip()

        text_equiv_parent = element.find("TextEquiv")
        if text_equiv_parent is not None:
            conf_attr = text_equiv_parent.get("conf")
            if conf_attr:
                try:
                    confidence = float(conf_attr)
                except ValueError:
                    pass

    display_text = text_content
    if confidence is not None:
        display_text = f"{text_content} ({confidence:.3f})"

    return display_text, confidence


def _extract_polygon_from_element(
    element: ET.Element, namespace: Optional[str], format_type: str
) -> List[Tuple[int, int]]:
    if format_type == "alto":
        shape = _find_child_element(element, "Shape", namespace)
        if shape is not None:
            polygon = _find_child_element(shape, "Polygon", namespace)
            if polygon is not None:
                points_str = polygon.get("POINTS", "")
                return _parse_points(points_str)

    elif format_type == "page":
        coords_elem = _find_child_element(element, "Coords", namespace)
        if coords_elem is not None:
            points_str = coords_elem.get("points", "")
            return _parse_points(points_str)

    return []


def _create_fallback_polygons(
    root: ET.Element, namespace: Optional[str]
) -> List[Tuple[str, List[Tuple[int, int]], str]]:
    elements_with_polygons = []

    for elem_type in ["String", "Word", "TextLine"]:
        elements = _find_elements_with_namespace(root, elem_type, namespace)

        for element in elements:
            coords = [element.get(attr) for attr in ["HPOS", "VPOS", "WIDTH", "HEIGHT"]]
            if all(coords):
                try:
                    x, y, w, h = map(int, coords)
                    points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]

                    text_content = element.get("CONTENT", "")
                    confidence = None
                    wc_attr = element.get("WC")
                    if wc_attr:
                        try:
                            confidence = float(wc_attr)
                        except ValueError:
                            pass

                    display_text = text_content
                    if confidence is not None:
                        display_text = f"{text_content} ({confidence:.3f})"

                    elements_with_polygons.append((elem_type, points, display_text))
                except ValueError:
                    continue

    return elements_with_polygons


def _draw_polygons(
    draw: ImageDraw.Draw,
    elements_with_polygons: List[Tuple[str, List[Tuple[int, int]], str]],
    font: Optional[ImageFont.FreeTypeFont],
):
    color_map = {
        "TextBlock": ["green", "purple"],
        "TextLine": ["red", "blue"],
        "String": ["orange", "cyan"],
        "Word": ["magenta", "yellow"],
    }

    for i, (elem_type, points, text_content) in enumerate(elements_with_polygons):
        colors = color_map.get(elem_type, ["black", "gray"])
        color = colors[i % 2]
        width_val = (
            3 if elem_type == "TextBlock" else 2 if elem_type == "TextLine" else 1
        )

        draw.polygon(points, outline=color, width=width_val, fill=None)

        if text_content and elem_type == "TextLine":
            centroid_x = sum(p[0] for p in points) // len(points)
            centroid_y = sum(p[1] for p in points) // len(points)

            if font:
                bbox = draw.textbbox((centroid_x, centroid_y), text_content, font=font)
                bbox = (bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2)
                draw.rectangle(bbox, fill=(255, 255, 255, 200), outline="black")
                draw.text(
                    (centroid_x, centroid_y), text_content, fill="black", font=font
                )
            else:
                draw.text((centroid_x, centroid_y), text_content, fill=color)


def _visualize_page_xml(
    draw: ImageDraw.Draw, root: ET.Element, image_size: Tuple[int, int]
):
    namespaces = {
        "ns": "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"
    }

    text_lines = root.findall(".//ns:TextLine", namespaces)
    if not text_lines:
        text_lines = root.findall(".//TextLine")

    line_data = []
    for text_line in text_lines:
        points = _extract_polygon_from_element(text_line, None, "page")
        if len(points) >= 3:
            display_text, _ = _extract_text_and_confidence(text_line, None, "page")
            line_data.append((points, display_text))

    textline_polygons = [points for points, _ in line_data]
    font_size = _get_dynamic_font_size(textline_polygons, image_size)
    font = _get_font(font_size)

    for i, (points, text) in enumerate(line_data):
        color = "red" if i % 2 == 0 else "blue"
        draw.polygon(points, outline=color, width=2, fill=None)

        if text:
            centroid_x = sum(p[0] for p in points) // len(points)
            centroid_y = sum(p[1] for p in points) // len(points)

            if font:
                bbox = draw.textbbox((centroid_x, centroid_y), text, font=font)
                bbox = (bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2)
                draw.rectangle(bbox, fill=(255, 255, 255, 200), outline="black")
                draw.text((centroid_x, centroid_y), text, fill="black", font=font)
            else:
                draw.text((centroid_x, centroid_y), text, fill=color)


def _visualize_alto_xml(
    draw: ImageDraw.Draw, root: ET.Element, image_size: Tuple[int, int]
):
    namespace = _get_namespace(root)
    elements_with_polygons = []

    text_blocks = _find_elements_with_namespace(root, "TextBlock", namespace)
    for text_block in text_blocks:
        points = _extract_polygon_from_element(text_block, namespace, "alto")
        if len(points) >= 3:
            text_block_id = text_block.get("ID", "")
            elements_with_polygons.append(
                ("TextBlock", points, f"TextBlock {text_block_id}")
            )

    text_lines = _find_elements_with_namespace(root, "TextLine", namespace)
    for text_line in text_lines:
        points = _extract_polygon_from_element(text_line, namespace, "alto")
        if len(points) >= 3:
            display_text, _ = _extract_text_and_confidence(text_line, namespace, "alto")
            elements_with_polygons.append(("TextLine", points, display_text))

    if not elements_with_polygons:
        elements_with_polygons = _create_fallback_polygons(root, namespace)

    textline_polygons = [
        points
        for elem_type, points, _ in elements_with_polygons
        if elem_type == "TextLine"
    ]
    font_size = _get_dynamic_font_size(textline_polygons, image_size)
    font = _get_font(font_size)

    _draw_polygons(draw, elements_with_polygons, font)
