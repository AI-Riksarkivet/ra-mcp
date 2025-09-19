# TODO add hf spaeces: https://huggingface.co/collections/Riksarkivet/mcps-68447208f9eddd623a83fbc9
# Perhaps markdown files should aslo be movedd to hf spaces as ressoure

from mcp.server.fastmcp import FastMCP
from gradio_client import Client
import sys
import io
import json 

mcp = FastMCP("gradio-spaces")

clients = {}

def get_client(space_id: str) -> Client:
    """Get or create a Gradio client for the specified space."""
    if space_id not in clients:
        clients[space_id] = Client(space_id)
    return clients[space_id]


@mcp.tool()
async def generate_image(prompt: str, space_id: str = "ysharma/SanaSprint") -> str:
    """Generate an image using Flux.
    
    Args:
        prompt: Text prompt describing the image to generate
        space_id: HuggingFace Space ID to use 
    """
    client = get_client(space_id)
    result = client.predict(
            prompt=prompt,
            model_size="1.6B",
            seed=0,
            randomize_seed=True,
            width=1024,
            height=1024,
            guidance_scale=4.5,
            num_inference_steps=2,
            api_name="/infer"
    )
    return result


@mcp.tool()
async def run_dia_tts(prompt: str, space_id: str = "ysharma/Dia-1.6B") -> str:
    """Text-to-Speech Synthesis.
    
    Args:
        prompt: Text prompt describing the conversation between speakers S1, S2
        space_id: HuggingFace Space ID to use 
    """
    client = get_client(space_id)
    result = client.predict(
            text_input=f"""{prompt}""",
            audio_prompt_input=None, 
            max_new_tokens=3072,
            cfg_scale=3,
            temperature=1.3,
            top_p=0.95,
            cfg_filter_top_k=30,
            speed_factor=0.94,
            api_name="/generate_audio"
    )
    return result
