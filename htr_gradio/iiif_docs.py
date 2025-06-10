import gradio as gr
import requests

"""
TODO: add https://github.com/AI-Riksarkivet/oxenstierna/tree/main iiifs and oah mp and search..
"""


def load_iiif_docs():
    """
    Get parts of iiif documentation, example code with Riksarkivet IIIF apis and useful context before answering questions or generating code. Should be used for general questions about iiif concepts and features of IIIF's Image API 3.0 and Presentation API 1.0 .

    Returns:
        str: IIIF's full documentation, example code with Riksarkivet IIIF apis, and useful context.
    """
    try:
        response = requests.get(
            "https://huggingface.co/spaces/Riksarkivet/iiif-mcp/raw/main/docs.md"
        )
        text = response.text
        return text
    except Exception as error:
        print(f"Error fetching document: {error}")
        return f"Error fetching document: {str(error)}"


with gr.Blocks() as demo:
    gr.HTML("<center><h1>IIIF Docs</h1></center>")
    with gr.Row():
        with gr.Column():
            load_button = gr.Button("Load IIIF Docs")

        with gr.Column():
            output = gr.Markdown()

    load_button.click(load_iiif_docs, outputs=output)

if __name__ == "__main__":
    demo.launch(mcp_server=True, strict_cors=False)
