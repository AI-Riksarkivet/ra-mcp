import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os
from typing import Optional, Tuple, List
import math


def htrflow_visualizer(image_path: str, htr_document_path: str, server_name: str = "https://gabriel-htrflow-mcp.hf.space") -> Optional[str]:
    """
    Visualize HTR results by overlaying text regions and polygons on the original image.

    Args:
        image_path (str): Path to the original document image file
        htr_document_path (str): Path to the HTR XML file (ALTO or PAGE format)

    Returns:
        str: File path to the generated visualization imagegenerated visualization image for direct download via gr.File (server_name/gradio_api/file=/tmp/gradio/{temp_folder}/{file_name})
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

    total_area = 0
    valid_count = 0

    for points in polygons:
        area = _calculate_polygon_area(points)
        if area > 0:
            total_area += area
            valid_count += 1

    if valid_count == 0:
        return 16

    avg_area = total_area / valid_count
    font_size = int(math.sqrt(avg_area) * 0.2)

    return max(12, min(72, font_size))


def _get_font(size: int) -> Optional[ImageFont.FreeTypeFont]:
    try:
        font_paths = [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)

        return ImageFont.load_default()
    except:
        return ImageFont.load_default()


def _get_namespace(root: ET.Element) -> Optional[str]:
    if "}" in root.tag:
        return root.tag.split("}")[0] + "}"
    return None


def _visualize_page_xml(
    draw: ImageDraw.Draw, root: ET.Element, image_size: Tuple[int, int]
):
    text_lines = []
    for elem in root.iter():
        if elem.tag.endswith("TextLine"):
            text_lines.append(elem)

    line_data = []
    all_polygons = []

    for text_line in text_lines:
        coords_elem = None
        for child in text_line:
            if child.tag.endswith("Coords"):
                coords_elem = child
                break

        if coords_elem is not None:
            points_str = coords_elem.get("points", "")
            points = _parse_points(points_str)

            if len(points) >= 3:
                text_content = ""
                confidence = None

                for te in text_line.iter():
                    if te.tag.endswith("Unicode") and te.text:
                        text_content = te.text.strip()
                        break

                for te in text_line.iter():
                    if te.tag.endswith("TextEquiv"):
                        conf_str = te.get("conf")
                        if conf_str:
                            try:
                                confidence = float(conf_str)
                            except:
                                pass
                        break

                display_text = text_content
                if confidence is not None:
                    display_text = f"{text_content} ({confidence:.3f})"

                line_data.append((points, display_text))
                all_polygons.append(points)

    font_size = _get_dynamic_font_size(all_polygons, image_size)
    font = _get_font(font_size)

    for i, (points, text) in enumerate(line_data):
        color = "red" if i % 2 == 0 else "blue"
        draw.polygon(points, outline=color, width=2)

        if text:
            centroid_x = sum(p[0] for p in points) // len(points)
            centroid_y = sum(p[1] for p in points) // len(points)

            if font != ImageFont.load_default():
                bbox = draw.textbbox(
                    (centroid_x, centroid_y), text, font=font, anchor="mm"
                )
                bbox = (bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2)
                draw.rectangle(bbox, fill=(255, 255, 255, 200), outline="black")
                draw.text(
                    (centroid_x, centroid_y), text, fill="black", font=font, anchor="mm"
                )
            else:
                draw.text((centroid_x, centroid_y), text, fill="black")


def _visualize_alto_xml(
    draw: ImageDraw.Draw, root: ET.Element, image_size: Tuple[int, int]
):
    namespace = _get_namespace(root)

    text_lines = []
    for elem in root.iter():
        if elem.tag.endswith("TextLine"):
            text_lines.append(elem)

    line_data = []
    all_polygons = []

    for text_line in text_lines:
        points = []
        for shape in text_line.iter():
            if shape.tag.endswith("Shape"):
                for polygon in shape.iter():
                    if polygon.tag.endswith("Polygon"):
                        points_str = polygon.get("POINTS", "")
                        points = _parse_points(points_str)
                        break
                break

        if len(points) >= 3:
            text_content = ""
            confidence = None

            for string_elem in text_line.iter():
                if string_elem.tag.endswith("String"):
                    text_content = string_elem.get("CONTENT", "")
                    wc_str = string_elem.get("WC")
                    if wc_str:
                        try:
                            confidence = float(wc_str)
                        except:
                            pass
                    break

            display_text = text_content
            if confidence is not None:
                display_text = f"{text_content} ({confidence:.3f})"

            line_data.append((points, display_text))
            all_polygons.append(points)

    font_size = _get_dynamic_font_size(all_polygons, image_size)
    font = _get_font(font_size)

    for i, (points, text) in enumerate(line_data):
        color = "red" if i % 2 == 0 else "blue"
        draw.polygon(points, outline=color, width=2)

        if text:
            centroid_x = sum(p[0] for p in points) // len(points)
            centroid_y = sum(p[1] for p in points) // len(points)

            if font != ImageFont.load_default():
                bbox = draw.textbbox(
                    (centroid_x, centroid_y), text, font=font, anchor="mm"
                )
                bbox = (bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2)
                draw.rectangle(bbox, fill=(255, 255, 255, 200), outline="black")
                draw.text(
                    (centroid_x, centroid_y), text, fill="black", font=font, anchor="mm"
                )
            else:
                draw.text((centroid_x, centroid_y), text, fill="black")
