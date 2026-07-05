"""Tests for ra_mcp_label_mcp.converter."""

import json

import pytest

from ra_mcp_label_mcp.converter import (
    _int,
    _parse_points,
    _polygon_from_baseline,
    convert_alto_to_tasks,
    parse_alto,
    tasks_to_json,
    to_label_studio_task,
)


# ---------------------------------------------------------------------------
# Minimal ALTO XML fixtures
# ---------------------------------------------------------------------------

ALTO_NS = """\
<?xml version="1.0" encoding="UTF-8"?>
<alto xmlns="http://www.loc.gov/standards/alto/ns-v4#">
  <Description><sourceImageInformation><fileName>page001.jpg</fileName></sourceImageInformation></Description>
  <Layout>
    <Page WIDTH="1000" HEIGHT="2000">
      <PrintSpace>
        <TextBlock>
          <TextLine ID="line1" HPOS="10" VPOS="20" WIDTH="200" HEIGHT="40">
            <Shape><Polygon POINTS="10,20 210,20 210,60 10,60"/></Shape>
            <String CONTENT="Hello"/>
            <String CONTENT="World"/>
          </TextLine>
        </TextBlock>
      </PrintSpace>
    </Page>
  </Layout>
</alto>
"""

ALTO_NO_NS = """\
<?xml version="1.0" encoding="UTF-8"?>
<alto>
  <Description><sourceImageInformation><fileName>nonamespace.jpg</fileName></sourceImageInformation></Description>
  <Layout>
    <Page WIDTH="500" HEIGHT="800">
      <PrintSpace>
        <TextBlock>
          <TextLine ID="tl_1" HPOS="5" VPOS="10" WIDTH="100" HEIGHT="20">
            <Shape><Polygon POINTS="5,10 105,10 105,30 5,30"/></Shape>
            <String CONTENT="NoNS"/>
          </TextLine>
        </TextBlock>
      </PrintSpace>
    </Page>
  </Layout>
</alto>
"""

ALTO_BASELINE_ONLY = """\
<?xml version="1.0" encoding="UTF-8"?>
<alto xmlns="http://www.loc.gov/standards/alto/ns-v4#">
  <Description><sourceImageInformation><fileName>baseline.jpg</fileName></sourceImageInformation></Description>
  <Layout>
    <Page WIDTH="600" HEIGHT="400">
      <PrintSpace>
        <TextBlock>
          <TextLine ID="bl1" BASELINE="100,200 300,200">
            <String CONTENT="Baseline"/>
            <String CONTENT="Only"/>
          </TextLine>
        </TextBlock>
      </PrintSpace>
    </Page>
  </Layout>
</alto>
"""

ALTO_BBOX_FALLBACK = """\
<?xml version="1.0" encoding="UTF-8"?>
<alto xmlns="http://www.loc.gov/standards/alto/ns-v4#">
  <Description><sourceImageInformation><fileName>bbox.jpg</fileName></sourceImageInformation></Description>
  <Layout>
    <Page WIDTH="800" HEIGHT="600">
      <PrintSpace>
        <TextBlock>
          <TextLine ID="bx1" HPOS="50" VPOS="100" WIDTH="200" HEIGHT="30">
            <String CONTENT="BBox"/>
          </TextLine>
        </TextBlock>
      </PrintSpace>
    </Page>
  </Layout>
</alto>
"""

ALTO_NO_TEXTLINES = """\
<?xml version="1.0" encoding="UTF-8"?>
<alto xmlns="http://www.loc.gov/standards/alto/ns-v4#">
  <Description><sourceImageInformation><fileName>empty.jpg</fileName></sourceImageInformation></Description>
  <Layout>
    <Page WIDTH="100" HEIGHT="100">
      <PrintSpace/>
    </Page>
  </Layout>
</alto>
"""

ALTO_MISSING_FILENAME = """\
<?xml version="1.0" encoding="UTF-8"?>
<alto xmlns="http://www.loc.gov/standards/alto/ns-v4#">
  <Description><sourceImageInformation/></Description>
  <Layout>
    <Page WIDTH="100" HEIGHT="100">
      <PrintSpace/>
    </Page>
  </Layout>
</alto>
"""

ALTO_NO_PAGE = """\
<?xml version="1.0" encoding="UTF-8"?>
<alto xmlns="http://www.loc.gov/standards/alto/ns-v4#">
  <Layout/>
</alto>
"""


# ---------------------------------------------------------------------------
# _int
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,default,expected",
    [
        pytest.param("42", 0, 42, id="normal-int"),
        pytest.param("0", 0, 0, id="zero-string"),
        pytest.param(None, 0, 0, id="none-default"),
        pytest.param("", 0, 0, id="empty-string-default"),
        pytest.param("abc", 0, 0, id="non-numeric-default"),
        pytest.param(None, 99, 99, id="none-custom-default"),
        pytest.param("abc", 5, 5, id="non-numeric-custom-default"),
        pytest.param("-10", 0, -10, id="negative-int"),
    ],
)
def test_int(value, default, expected):
    assert _int(value, default) == expected


# ---------------------------------------------------------------------------
# _parse_points
# ---------------------------------------------------------------------------


def test_parse_points_standard():
    assert _parse_points("10,20 30,40 50,60") == [(10, 20), (30, 40), (50, 60)]


def test_parse_points_single():
    assert _parse_points("100,200") == [(100, 200)]


def test_parse_points_leading_trailing_whitespace():
    assert _parse_points("  10,20  30,40  ") == [(10, 20), (30, 40)]


# ---------------------------------------------------------------------------
# _polygon_from_baseline
# ---------------------------------------------------------------------------


def test_polygon_from_baseline_two_points():
    polygon = _polygon_from_baseline("100,200 300,200")
    assert polygon == "100,160 300,160 300,215 100,215"


def test_polygon_from_baseline_custom_offsets():
    polygon = _polygon_from_baseline("100,200 300,200", ascent=10, descent=5)
    assert polygon == "100,190 300,190 300,205 100,205"


def test_polygon_from_baseline_clamps_y_to_zero():
    polygon = _polygon_from_baseline("100,20 300,20", ascent=40, descent=15)
    assert "100,0" in polygon


def test_polygon_from_baseline_single_point_returns_empty():
    assert _polygon_from_baseline("100,200") == ""


def test_polygon_from_baseline_empty_string():
    assert _polygon_from_baseline("") == ""


def test_polygon_from_baseline_invalid_data():
    assert _polygon_from_baseline("not,valid nope") == ""


def test_polygon_from_baseline_three_points():
    polygon = _polygon_from_baseline("100,200 200,200 300,200")
    parts = polygon.split()
    assert len(parts) == 6


# ---------------------------------------------------------------------------
# parse_alto — namespaced
# ---------------------------------------------------------------------------


def test_parse_alto_namespaced():
    result = parse_alto(ALTO_NS)
    assert result["filename"] == "page001.jpg"
    assert result["page_width"] == 1000
    assert result["page_height"] == 2000
    assert len(result["textlines"]) == 1

    tl = result["textlines"][0]
    assert tl["text"] == "Hello World"
    assert tl["id"] == "line1"
    assert tl["points"] == [(10, 20), (210, 20), (210, 60), (10, 60)]


# ---------------------------------------------------------------------------
# parse_alto — no namespace
# ---------------------------------------------------------------------------


def test_parse_alto_no_namespace():
    result = parse_alto(ALTO_NO_NS)
    assert result["filename"] == "nonamespace.jpg"
    assert result["page_width"] == 500
    assert result["page_height"] == 800
    assert len(result["textlines"]) == 1
    assert result["textlines"][0]["text"] == "NoNS"


# ---------------------------------------------------------------------------
# parse_alto — polygon fallback chain
# ---------------------------------------------------------------------------


def test_parse_alto_baseline_fallback():
    result = parse_alto(ALTO_BASELINE_ONLY)
    assert result["filename"] == "baseline.jpg"
    assert len(result["textlines"]) == 1
    tl = result["textlines"][0]
    assert tl["text"] == "Baseline Only"
    assert len(tl["points"]) > 2


def test_parse_alto_bbox_fallback():
    result = parse_alto(ALTO_BBOX_FALLBACK)
    assert len(result["textlines"]) == 1
    tl = result["textlines"][0]
    assert tl["points"] == [(50, 100), (250, 100), (250, 130), (50, 130)]
    assert tl["text"] == "BBox"


# ---------------------------------------------------------------------------
# parse_alto — edge cases
# ---------------------------------------------------------------------------


def test_parse_alto_no_textlines():
    result = parse_alto(ALTO_NO_TEXTLINES)
    assert result["textlines"] == []
    assert result["filename"] == "empty.jpg"


def test_parse_alto_missing_filename():
    result = parse_alto(ALTO_MISSING_FILENAME)
    assert result["filename"] == "unknown"


def test_parse_alto_no_page_raises():
    with pytest.raises(ValueError, match="No <Page> element"):
        parse_alto(ALTO_NO_PAGE)


# ---------------------------------------------------------------------------
# to_label_studio_task
# ---------------------------------------------------------------------------


_DEFAULT_TEXTLINES = [
    {
        "points": [(100, 200), (300, 200), (300, 250), (100, 250)],
        "text": "Sample text",
        "id": "tl1",
    }
]


def _make_parsed(textlines=None, width=1000, height=2000, filename="test.jpg"):
    return {
        "filename": filename,
        "page_width": width,
        "page_height": height,
        "textlines": _DEFAULT_TEXTLINES if textlines is None else textlines,
    }


def test_to_label_studio_task_with_image_url():
    parsed = _make_parsed()
    task = to_label_studio_task(parsed, image_url="https://example.com/page.jpg")

    assert task["data"]["ocr"] == "https://example.com/page.jpg"
    assert "predictions" in task
    assert len(task["predictions"]) == 1
    results = task["predictions"][0]["result"]
    assert len(results) == 2
    assert results[0]["type"] == "vectorlabels"
    assert results[1]["type"] == "textarea"


def test_to_label_studio_task_default_image_url():
    parsed = _make_parsed()
    task = to_label_studio_task(parsed)
    assert task["data"]["ocr"] == "/data/local-files/?d=test.jpg"


def test_to_label_studio_task_vectorlabels_structure():
    parsed = _make_parsed()
    task = to_label_studio_task(parsed, image_url="https://img.test/1.jpg")
    vl = task["predictions"][0]["result"][0]

    assert vl["from_name"] == "label"
    assert vl["to_name"] == "image"
    assert vl["original_width"] == 1000
    assert vl["original_height"] == 2000
    assert vl["image_rotation"] == 0
    assert vl["value"]["closed"] is True
    assert vl["value"]["vectorlabels"] == ["Textlines"]

    vertices = vl["value"]["vertices"]
    assert len(vertices) == 4
    assert vertices[0]["x"] == pytest.approx(10.0)
    assert vertices[0]["y"] == pytest.approx(10.0)
    assert vertices[0]["isBezier"] is False
    assert vertices[0]["prevPointId"] is None
    assert vertices[1]["prevPointId"] == vertices[0]["id"]


def test_to_label_studio_task_textarea_structure():
    parsed = _make_parsed()
    task = to_label_studio_task(parsed, image_url="https://img.test/1.jpg")
    ta = task["predictions"][0]["result"][1]

    assert ta["type"] == "textarea"
    assert ta["from_name"] == "transcription"
    assert ta["value"]["text"] == ["Sample text"]


def test_to_label_studio_task_with_feedback():
    parsed = _make_parsed()
    task = to_label_studio_task(parsed, image_url="https://img.test/1.jpg", feedback=["Transcription"])
    results = task["predictions"][0]["result"]
    assert len(results) == 3
    fb = results[2]
    assert fb["type"] == "choices"
    assert fb["from_name"] == "feedback"
    assert fb["value"]["choices"] == ["Transcription"]


def test_to_label_studio_task_with_multiple_feedback():
    parsed = _make_parsed()
    task = to_label_studio_task(
        parsed,
        image_url="https://img.test/1.jpg",
        feedback=["Transcription", "Segmentation"],
    )
    fb = task["predictions"][0]["result"][2]
    assert fb["value"]["choices"] == ["Transcription", "Segmentation"]


def test_to_label_studio_task_no_feedback_means_two_results():
    parsed = _make_parsed()
    task = to_label_studio_task(parsed, image_url="https://img.test/1.jpg", feedback=None)
    assert len(task["predictions"][0]["result"]) == 2


def test_to_label_studio_task_empty_textlines():
    parsed = _make_parsed(textlines=[])
    task = to_label_studio_task(parsed, image_url="https://img.test/1.jpg")
    assert task["predictions"][0]["result"] == []


def test_to_label_studio_task_region_ids_shared():
    """VectorLabels and textarea for same textline share the same region ID."""
    parsed = _make_parsed()
    task = to_label_studio_task(parsed, image_url="https://img.test/1.jpg")
    results = task["predictions"][0]["result"]
    assert results[0]["id"] == results[1]["id"]


def test_to_label_studio_task_multiple_textlines():
    parsed = _make_parsed(
        textlines=[
            {"points": [(0, 0), (100, 0), (100, 50), (0, 50)], "text": "Line 1", "id": "l1"},
            {"points": [(0, 60), (100, 60), (100, 110), (0, 110)], "text": "Line 2", "id": "l2"},
        ]
    )
    task = to_label_studio_task(parsed, image_url="https://img.test/1.jpg")
    results = task["predictions"][0]["result"]
    assert len(results) == 4
    assert results[0]["id"] != results[2]["id"]


def test_to_label_studio_task_percentage_coordinates():
    """Coordinates are converted from absolute pixels to percentages of page dimensions."""
    parsed = _make_parsed(
        textlines=[
            {"points": [(500, 1000)], "text": "center", "id": "c"},
        ],
        width=1000,
        height=2000,
    )
    task = to_label_studio_task(parsed, image_url="https://img.test/1.jpg")
    vertex = task["predictions"][0]["result"][0]["value"]["vertices"][0]
    assert vertex["x"] == pytest.approx(50.0)
    assert vertex["y"] == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# convert_alto_to_tasks
# ---------------------------------------------------------------------------


def test_convert_alto_to_tasks_single():
    tasks = convert_alto_to_tasks([ALTO_NS], image_urls=["https://img.test/1.jpg"])
    assert len(tasks) == 1
    assert tasks[0]["data"]["ocr"] == "https://img.test/1.jpg"
    assert len(tasks[0]["predictions"][0]["result"]) == 2


def test_convert_alto_to_tasks_multiple():
    tasks = convert_alto_to_tasks(
        [ALTO_NS, ALTO_NO_NS],
        image_urls=["https://img.test/1.jpg", "https://img.test/2.jpg"],
    )
    assert len(tasks) == 2
    assert tasks[0]["data"]["ocr"] == "https://img.test/1.jpg"
    assert tasks[1]["data"]["ocr"] == "https://img.test/2.jpg"


def test_convert_alto_to_tasks_no_image_urls():
    tasks = convert_alto_to_tasks([ALTO_NS])
    assert tasks[0]["data"]["ocr"] == "/data/local-files/?d=page001.jpg"


def test_convert_alto_to_tasks_with_feedback():
    tasks = convert_alto_to_tasks(
        [ALTO_NS],
        image_urls=["https://img.test/1.jpg"],
        feedback_list=[["Transcription"]],
    )
    results = tasks[0]["predictions"][0]["result"]
    assert any(r["type"] == "choices" for r in results)


def test_convert_alto_to_tasks_partial_image_urls():
    tasks = convert_alto_to_tasks(
        [ALTO_NS, ALTO_NO_NS],
        image_urls=["https://img.test/1.jpg"],
    )
    assert tasks[0]["data"]["ocr"] == "https://img.test/1.jpg"
    assert tasks[1]["data"]["ocr"] == "/data/local-files/?d=nonamespace.jpg"


# ---------------------------------------------------------------------------
# tasks_to_json
# ---------------------------------------------------------------------------


def test_tasks_to_json_valid():
    tasks = [{"data": {"ocr": "https://example.com/img.jpg"}}]
    result = tasks_to_json(tasks)
    parsed = json.loads(result)
    assert parsed == tasks


def test_tasks_to_json_ensure_ascii_false():
    tasks = [{"data": {"ocr": "https://example.com/åäö.jpg"}}]
    result = tasks_to_json(tasks)
    assert "åäö" in result


def test_tasks_to_json_empty_list():
    result = tasks_to_json([])
    assert json.loads(result) == []
