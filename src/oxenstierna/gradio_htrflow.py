import gradio as gr
import json
import tempfile
import os
from typing import List, Optional, Literal
from PIL import Image
import spaces
from pathlib import Path
from htrflow.volume.volume import Collection
from htrflow.pipeline.pipeline import Pipeline

DEFAULT_OUTPUT = "alto"
CHOICES = ["txt", "alto", "page", "json"]

PIPELINE_CONFIGS = {
    "letter_english": {
        "steps": [
            {
                "step": "Segmentation",
                "settings": {
                    "model": "yolo",
                    "model_settings": {"model": "Riksarkivet/yolov9-lines-within-regions-1"},
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
                    "model_settings": {"model": "Riksarkivet/yolov9-lines-within-regions-1"},
                    "generation_settings": {"batch_size": 8},
                },
            },
            {
                "step": "TextRecognition",
                "settings": {
                    "model": "TrOCR",
                    "model_settings": {"model": "Riksarkivet/trocr-base-handwritten-hist-swe-2"},
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
                    "model_settings": {"model": "Riksarkivet/yolov9-lines-within-regions-1"},
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
                    "model_settings": {"model": "Riksarkivet/yolov9-lines-within-regions-1"},
                    "generation_settings": {"batch_size": 8},
                },
            },
            {
                "step": "TextRecognition",
                "settings": {
                    "model": "TrOCR",
                    "model_settings": {"model": "Riksarkivet/trocr-base-handwritten-hist-swe-2"},
                    "generation_settings": {"batch_size": 16},
                },
            },
            {"step": "ReadingOrderMarginalia", "settings": {"two_page": True}},
        ]
    },
}

@spaces.GPU
def htrflow_htr_url(image_path: str, document_type: Literal["letter_english", "letter_swedish", "spread_english", "spread_swedish"] = "letter_swedish", output_format: Literal["txt", "alto", "page", "json"] = DEFAULT_OUTPUT, custom_settings: Optional[str] = None) -> str:
    """
    Process handwritten text recognition (HTR) on uploaded images and return both file content and download link.
    
    This function uses machine learning models to automatically detect, segment, and transcribe handwritten text 
    from historical documents. It supports different document types and languages, with specialized models 
    trained on historical handwriting from the Swedish National Archives (Riksarkivet).
    
    Args:
        image_path (str): The file path or URL to the image containing handwritten text to be processed.
                         Supports common image formats like JPG, PNG, TIFF.
        
        document_type (Literal): The type of document and language processing template to use.
                                Available options:
                                - "letter_english": Single-page English handwritten letters
                                - "letter_swedish": Single-page Swedish handwritten letters (default)
                                - "spread_english": Two-page spread English documents with marginalia
                                - "spread_swedish": Two-page spread Swedish documents with marginalia
                                Default: "letter_swedish"
        
        output_format (Literal): The format for the output file containing the transcribed text.
                                Available options:
                                - "txt": Plain text format with line breaks
                                - "alto": ALTO XML format with detailed layout and coordinate information
                                - "page": PAGE XML format with structural markup and positioning data  
                                - "json": JSON format with structured text, layout information and metadata
                                Default: "alto"
        
        custom_settings (Optional[str]): Advanced users can provide custom pipeline configuration as a 
                                        JSON string to override the default processing steps.
                                        Default: None (uses predefined configuration for document_type)
        
    Returns:
        str: JSON string containing both the file content and download link:
             {
                 "content": "file_content_here",
                 "file_path": "[file_name](http://your-server:port/gradio_api//file=/tmp/gradio/{temp_folder}/{file_name}.{file_format})"
             }
    """
    if not image_path:
        return json.dumps({"error": "No image provided"})

    try:
        original_filename = Path(image_path).stem or "output"
        
        if custom_settings:
            try:
                config = json.loads(custom_settings)
            except json.JSONDecodeError:
                return json.dumps({"error": "Invalid JSON in custom_settings parameter"})
        else:
            config = PIPELINE_CONFIGS[document_type]

        collection = Collection([image_path])
        pipeline = Pipeline.from_config(config)
        
        try:
            processed_collection = pipeline.run(collection)
        except Exception as pipeline_error:
            return json.dumps({"error": f"Pipeline execution failed: {str(pipeline_error)}"})

        temp_dir = Path(tempfile.mkdtemp())
        export_dir = temp_dir / output_format
        processed_collection.save(directory=str(export_dir), serializer=output_format)
        
        output_file_path = None
        for root, _, files in os.walk(export_dir):
            for file in files:
                old_path = os.path.join(root, file)
                file_ext = Path(file).suffix
                new_filename = f"{original_filename}.{output_format}" if not file_ext else f"{original_filename}{file_ext}"
                new_path = os.path.join(root, new_filename)
                os.rename(old_path, new_path)
                output_file_path = new_path
                break
        
        if output_file_path and os.path.exists(output_file_path):

            with open(output_file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            
            file_name = Path(output_file_path).name
            temp_folder = Path(output_file_path).parent.name
            markdown_link = f"[{file_name}](http://your-server:port/gradio_api//file=/tmp/gradio/{temp_folder}/{file_name})"
            
            result = {
                "content": file_content,
                "file_path": markdown_link
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            return json.dumps({"error": "Failed to generate output file"})
        
    except Exception as e:
        return json.dumps({"error": f"HTR processing failed: {str(e)}"})
    
    
def htrflow_visualizer(image: str, htr_document: str) -> str:
    pass

def extract_text_from_collection(collection: Collection) -> str:
    text_lines = []
    for page in collection.pages:
        for node in page.traverse():
            if hasattr(node, "text") and node.text:
                text_lines.append(node.text)
    return "\n".join(text_lines)

def create_htrflow_mcp_server():
    htrflow_url = gr.Interface(
        fn=htrflow_htr_url,
        inputs=[
            gr.Image(type="filepath", label="Upload Image or Enter URL"),
            gr.Dropdown(choices=["letter_english", "letter_swedish", "spread_english", "spread_swedish"], value="letter_swedish", label="Document Type"),
            gr.Dropdown(choices=CHOICES, value=DEFAULT_OUTPUT, label="Output Format"),
            gr.Textbox(label="Custom Settings (JSON)", placeholder="Optional custom pipeline settings", value=""),
        ],
        outputs=gr.Textbox(label="HTR Result (JSON)", lines=10),
        description="Process handwritten text from uploaded file or URL and get both content and download link in JSON format",
        api_name="htrflow_htr_url",
    )

    htrflow_viz = gr.Interface(
        fn=htrflow_visualizer,
        inputs=[
            gr.Image(type="filepath", label="Upload Image or Enter URL"),
            gr.Textbox(label="HTR Document content", placeholder="Path to the HTR document file", value=""),
        ],
        outputs=gr.File(label="Download Output File"),
        description="Visualize document",
        api_name="htrflow_visualizer"
    )

    demo = gr.TabbedInterface(
        [htrflow_url, htrflow_viz],
        ["HTR URL", "HTR Visualizer"],
        title="HTRflow Handwritten Text Recognition",
    )

    return demo

if __name__ == "__main__":
    demo = create_htrflow_mcp_server()
    demo.launch(mcp_server=True, share=False, debug=False)