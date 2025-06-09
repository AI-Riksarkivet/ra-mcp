from typing import Optional, Tuple
from fastmcp import FastMCP
from gradio_client import Client, handle_file

htr_server = FastMCP(
    name="htr_server",
    instructions="""
    Handwritten Text Recognition (HTR) server for historical documents.
    
    Uses machine learning models to automatically detect, segment, and transcribe 
    handwritten text from historical documents, with specialized models trained 
    on Swedish National Archives materials.
    """,
)


@htr_server.tool()
async def generate_image(
    image_path: str,
    document_type: str = "letter_swedish",
    output_format: str = "alto",
    custom_settings: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Process handwritten text recognition (HTR) on uploaded images and return both file content and download link.

    This function uses machine learning models to automatically detect, segment, and transcribe handwritten text
    from historical documents. It supports different document types and languages, with specialized models
    trained on historical handwriting from the Swedish National Archives (Riksarkivet).

    Args:
        image_path (str): The file path or URL to the image containing handwritten text to be processed.
                         Supports common image formats like JPG, PNG, TIFF.

        document_type (FormatChoices): The type of document and language processing template to use.
                                Available options:
                                - "letter_english": Single-page English handwritten letters
                                - "letter_swedish": Single-page Swedish handwritten letters (default)
                                - "spread_english": Two-page spread English documents with marginalia
                                - "spread_swedish": Two-page spread Swedish documents with marginalia
                                Default: "letter_swedish"

        output_format (FileChoices): The format for the output file containing the transcribed text.
                                Available options:
                                - "txt": Plain text format with line breaks
                                - "alto": ALTO XML format with detailed layout and coordinate information
                                - "page": PAGE XML format with structural markup and positioning data
                                - "json": JSON format with structured text, layout information and metadata
                                Default: "alto"

        custom_settings (Optional[str]): Advanced users can provide custom pipeline configuration as a
                                        JSON string to override the default processing steps.
                                        Default: None (uses predefined configuration for document_type)

        server_name (str): The base URL of the server for constructing download links.
                          Default: "https://gabriel-htrflow-mcp.hf.space"

            Returns:
        Tuple[str, str]: A tuple containing:
            - JSON string with extracted text, file content
            - File path for direct download via gr.File (server_name/gradio_api/file=/tmp/gradio/{temp_folder}/{file_name})
    """

    client = Client("Gabriel/htrflow_mcp")
    result = client.predict(
        image_path=handle_file(image_path),
        document_type=document_type,
        output_format=output_format,
        custom_settings=custom_settings or "",
        api_name="/htrflow_htr_url",
    )
    return result
