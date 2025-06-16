from fastmcp import FastMCP
from phoenix.otel import register
from typing import Optional, Tuple
from gradio_client import handle_file, Client

from oxenstierna.search_server import search_mcp
from oxenstierna.iiif_server import iiif_mcp

mcp = FastMCP("My App")

mcp.mount("search", search_mcp)
mcp.mount("iiif", iiif_mcp)


tracer_provider = register(
    auto_instrument=True,
    endpoint="http://localhost:6006/v1/traces",
)

tracer = tracer_provider.get_tracer("demo-tracer")



@mcp.tool()
@tracer.tool(name="MCP.htr_text")
async def htr_text(
    image_path: str,
    document_type: str = "letter_swedish",
    custom_settings: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Process handwritten text recognition (HTR) on uploaded images and return the text in str

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

        custom_settings (Optional[str]): Advanced users can provide custom pipeline settings as a JSON string.

            Returns: str
    """

    client = Client("Gabriel/htrflow_mcp")
    result = client.predict(
        image_path=handle_file(image_path),
        document_type=document_type,
        custom_settings=custom_settings or "",
        api_name="/htr_text",
    )
    return result


@mcp.tool()
@tracer.tool(name="MCP.htrflow_visualizer")
async def htrflow_visualizer(image_path: str, htr_document_path: str, server_name: str = "https://gabriel-htrflow-mcp.hf.space") -> Optional[str]:
    """
    Visualize HTR results by overlaying text regions and polygons on the original image.
    Args:
        image_path (str): Path to the original document image file
        htr_document_path (str): Path to the HTR XML file (ALTO or PAGE format)
    Returns:
        str: File path to the generated visualization imagegenerated visualization image for direct download via gr.File (server_name/gradio_api/file=/tmp/gradio/{temp_folder}/{file_name})
        e.g : https://gabriel-htrflow-mcp.hf.space/gradio_api/file=/tmp/gradio/34d5c1a8b7d5445469c4f7c638c490e0e3046b3008a0182f89c688b1b42d139b/htr_visualization.png
    """
    client = Client("Gabriel/htrflow_mcp")
    result = client.predict(
        image_path=handle_file(image_path),
        htr_document_path=handle_file(htr_document_path),
		server_name="https://gabriel-htrflow-mcp.hf.space",
        api_name="/htrflow_visualizer",
    )
    return result


@mcp.resource("resource://iiif")
async def iiif_docs() -> Optional[str]:
    """
    Visualize HTR results by overlaying text regions and polygons on the original image.
    Args:
        image_path (str): Path to the original document image file
        htr_document_path (str): Path to the HTR XML file (ALTO or PAGE format)
    Returns:
        str: File path to the generated visualization imagegenerated visualization image for direct download via gr.File (server_name/gradio_api/file=/tmp/gradio/{temp_folder}/{file_name})
        e.g : https://gabriel-htrflow-mcp.hf.space/gradio_api/file=/tmp/gradio/34d5c1a8b7d5445469c4f7c638c490e0e3046b3008a0182f89c688b1b42d139b/htr_visualization.png
    """
    client = Client("Riksarkivet/iiif_mcp_docs")
    result = client.predict(

        api_name="/load_iiif_docs",
    )
    return result


@mcp.tool()
@tracer.tool(name="MCP.htrflow_file")
async def htrflow_file(
    image_path: str,
    document_type: str = "letter_swedish",
    output_format: str = "alto",
    custom_settings: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Process handwritten text recognition (HTR) on uploaded images and return both file content and download link.

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

        custom_settings (Optional[str]): Advanced users can provide custom pipeline settings as a JSON string.

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
        api_name="/htrflow_file",
    )
    return result

@mcp.tool()
@tracer.tool(name="MCP.fetch_weather")
async def fetch_weather(city: str) -> str:
    """Fetch current weather for a city"""
    # Mock weather data
    weather_data = {
        "paris": "Sunny 😎, 22°C",
        "london": "Rainy, 15°C",
        "tokyo": "Cloudy, 18°C",
    }
    return weather_data.get(city.lower(), f"No weather data available for {city}")



if __name__ == "__main__":
    mcp.run()
