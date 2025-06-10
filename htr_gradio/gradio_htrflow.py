import gradio as gr
import json
import tempfile
import os
from typing import List, Optional, Literal, Tuple
from PIL import Image

# import spaces
from pathlib import Path
from visualizer import htrflow_visualizer


DEFAULT_OUTPUT = "alto"
FORMAT_CHOICES = [
    "letter_english",
    "letter_swedish",
    "spread_english",
    "spread_swedish",
]
FILE_CHOICES = ["txt", "alto", "page", "json"]

FormatChoices = Literal[
    "letter_english", "letter_swedish", "spread_english", "spread_swedish"
]
FileChoices = Literal["txt", "alto", "page", "json"]

PIPELINE_CONFIGS = {
    "letter_english": {
        "steps": [
            {
                "step": "Segmentation",
                "settings": {
                    "model": "yolo",
                    "model_settings": {
                        "model": "Riksarkivet/yolov9-lines-within-regions-1"
                    },
                    "generation_settings": {"batch_size": 8},
                },
            },
            {
                "step": "TextRecognition",
                "settings": {
                    "model": "TrOCR",
                    "model_settings": {"model": "microsoft/trocr-base-handwritten"},
                    "generation_settings": {"batch_size": 16},
                },
            },
            {"step": "OrderLines"},
        ]
    },
    "letter_swedish": {
        "steps": [
            {
                "step": "Segmentation",
                "settings": {
                    "model": "yolo",
                    "model_settings": {
                        "model": "Riksarkivet/yolov9-lines-within-regions-1"
                    },
                    "generation_settings": {"batch_size": 8},
                },
            },
            {
                "step": "TextRecognition",
                "settings": {
                    "model": "TrOCR",
                    "model_settings": {
                        "model": "Riksarkivet/trocr-base-handwritten-hist-swe-2"
                    },
                    "generation_settings": {"batch_size": 16},
                },
            },
            {"step": "OrderLines"},
        ]
    },
    "spread_english": {
        "steps": [
            {
                "step": "Segmentation",
                "settings": {
                    "model": "yolo",
                    "model_settings": {"model": "Riksarkivet/yolov9-regions-1"},
                    "generation_settings": {"batch_size": 4},
                },
            },
            {
                "step": "Segmentation",
                "settings": {
                    "model": "yolo",
                    "model_settings": {
                        "model": "Riksarkivet/yolov9-lines-within-regions-1"
                    },
                    "generation_settings": {"batch_size": 8},
                },
            },
            {
                "step": "TextRecognition",
                "settings": {
                    "model": "TrOCR",
                    "model_settings": {"model": "microsoft/trocr-base-handwritten"},
                    "generation_settings": {"batch_size": 16},
                },
            },
            {"step": "ReadingOrderMarginalia", "settings": {"two_page": True}},
        ]
    },
    "spread_swedish": {
        "steps": [
            {
                "step": "Segmentation",
                "settings": {
                    "model": "yolo",
                    "model_settings": {"model": "Riksarkivet/yolov9-regions-1"},
                    "generation_settings": {"batch_size": 4},
                },
            },
            {
                "step": "Segmentation",
                "settings": {
                    "model": "yolo",
                    "model_settings": {
                        "model": "Riksarkivet/yolov9-lines-within-regions-1"
                    },
                    "generation_settings": {"batch_size": 8},
                },
            },
            {
                "step": "TextRecognition",
                "settings": {
                    "model": "TrOCR",
                    "model_settings": {
                        "model": "Riksarkivet/trocr-base-handwritten-hist-swe-2"
                    },
                    "generation_settings": {"batch_size": 16},
                },
            },
            {"step": "ReadingOrderMarginalia", "settings": {"two_page": True}},
        ]
    },
}

# @spaces.GPU
# def _process_htr_pipeline(image_path: str, document_type: FormatChoices, custom_settings: Optional[str] = None) -> Collection:
#     """Process HTR pipeline and return the processed collection."""

#     if not image_path:
#         raise ValueError("No image provided")

#     if custom_settings:
#         try:
#             config = json.loads(custom_settings)
#         except json.JSONDecodeError:
#             raise ValueError("Invalid JSON in custom_settings parameter")
#     else:
#         config = PIPELINE_CONFIGS[document_type]

#     collection = Collection([image_path])
#     pipeline = Pipeline.from_config(config)

#     try:
#         processed_collection = pipeline.run(collection)
#         return processed_collection
#     except Exception as pipeline_error:
#         raise RuntimeError(f"Pipeline execution failed: {str(pipeline_error)}")


def htr_text(
    image_path: str,
    document_type: FormatChoices = "letter_swedish",
    custom_settings: Optional[str] = None,
) -> str:
    """Extract text from handwritten documents using HTR.
    
    returns:
        str: Extracted text from the image.
    """
    try:
        processed_collection = _process_htr_pipeline(
            image_path, document_type, custom_settings
        )
        extracted_text = extract_text_from_collection(processed_collection)
        return extracted_text

    except Exception as e:
        return f"HTR text extraction failed: {str(e)}"


def htrflow_file(
    image_path: str,
    document_type: FormatChoices = "letter_swedish",
    output_format: FileChoices = DEFAULT_OUTPUT,
    custom_settings: Optional[str] = None,
    server_name: str = "https://gabriel-htrflow-mcp.hf.space",
) -> str:
    """
    Process HTR and return a formatted file for download.

    Returns:
        str: File path for direct download via gr.File (server_name/gradio_api/file=/tmp/gradio/{temp_folder}/{file_name})
    """
    try:
        original_filename = Path(image_path).stem or "output"

        processed_collection = _process_htr_pipeline(
            image_path, document_type, custom_settings
        )

        temp_dir = Path(tempfile.mkdtemp())
        export_dir = temp_dir / output_format
        processed_collection.save(directory=str(export_dir), serializer=output_format)

        output_file_path = None
        for root, _, files in os.walk(export_dir):
            for file in files:
                old_path = os.path.join(root, file)
                file_ext = Path(file).suffix
                new_filename = (
                    f"{original_filename}.{output_format}"
                    if not file_ext
                    else f"{original_filename}{file_ext}"
                )
                new_path = os.path.join(root, new_filename)
                os.rename(old_path, new_path)
                output_file_path = new_path
                break

        if output_file_path and os.path.exists(output_file_path):
            return output_file_path
        else:
            return None

    except Exception as e:
        return None


# def extract_text_from_collection(collection: Collection) -> str:
#     text_lines = []
#     for page in collection.pages:
#         for node in page.traverse():
#             if hasattr(node, "text") and node.text:
#                 text_lines.append(node.text)
#     return "\n".join(text_lines)


def create_htrflow_mcp_server():
    htr_text_interface = gr.Interface(
        fn=htr_text,
        inputs=[
            gr.Image(type="filepath", label="Upload Image or Enter URL"),
            gr.Dropdown(
                choices=FORMAT_CHOICES, value="letter_swedish", label="Document Type"
            ),
            gr.Textbox(
                label="Custom Settings (JSON)",
                placeholder="Optional custom pipeline settings",
                value="",
            ),
        ],
        outputs=[gr.Textbox(label="Extracted Text", lines=10)],
        description="Extract plain text from handwritten documents using HTR",
        api_name="htr_text",
    )

    htrflow_file_interface = gr.Interface(
        fn=htrflow_file,
        inputs=[
            gr.Image(type="filepath", label="Upload Image or Enter URL"),
            gr.Dropdown(
                choices=FORMAT_CHOICES, value="letter_swedish", label="Document Type"
            ),
            gr.Dropdown(
                choices=FILE_CHOICES, value=DEFAULT_OUTPUT, label="Output Format"
            ),
            gr.Textbox(
                label="Custom Settings (JSON)",
                placeholder="Optional custom pipeline settings",
                value="",
            ),
            gr.Textbox(
                label="Server Name",
                value="https://gabriel-htrflow-mcp.hf.space",
                placeholder="Server URL for download links",
            ),
        ],
        outputs=[gr.File(label="Download HTR Output File")],
        description="Process handwritten text and get formatted file (ALTO XML, PAGE XML, JSON, or TXT)",
        api_name="htrflow_file",
    )

    htrflow_viz = gr.Interface(
        fn=htrflow_visualizer,
        inputs=[
            gr.Image(type="filepath", label="Upload Original Image"),
            gr.File(label="Upload ALTO/PAGE XML File"),
            gr.Textbox(
                label="Server Name",
                value="https://gabriel-htrflow-mcp.hf.space",
                placeholder="Server URL for download links",
            ),
        ],
        outputs=gr.File(label="Download Visualization Image"),
        description="Visualize HTR results by overlaying text regions and polygons on the original image",
        api_name="htrflow_visualizer",
    )

    demo = gr.TabbedInterface(
        [htr_text_interface, htrflow_file_interface, htrflow_viz],
        ["HTR Text", "HTR File", "HTR Visualizer"],
        title="HTRflow Handwritten Text Recognition",
    )

    return demo


if __name__ == "__main__":
    demo = create_htrflow_mcp_server()
    demo.launch(mcp_server=True, share=False, debug=False)
