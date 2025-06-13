import json
import asyncio
import os
import subprocess
import tempfile
from anthropic import AsyncAnthropic
from typing import Any, List, Dict
import gradio as gr

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

# Anthropic Configuration
MODEL_ID = os.getenv("MODEL_ID", "claude-sonnet-4-20250514")

class MCPClientWrapper:
    """Wrapper class using Anthropic's native MCP support"""
    
    def __init__(self):
        self.client = AsyncAnthropic(api_key=anthropic_api_key)
        self.server_url = "https://62b7-2001-1ba8-1420-9f00-6c8c-7027-b171-610e.ngrok-free.app"
        self.connected = False
    
    def connect(self, server_info: str):
        """Connect to HTTP MCP server"""
        # For now, we'll use a fixed URL
        self.connected = True
        return f"✅ Ready to use MCP server at: {self.server_url}"
    
    def process_message(self, message: str, history: List[Dict[str, Any]]):
        """Process message using Anthropic's native MCP support"""
        if not message.strip():
            yield history
            return
            
        if not self.connected:
            yield history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": "❌ Please connect to an MCP server first."}
            ]
            return
        
        # Immediately show user message
        history = history + [{"role": "user", "content": message}]
        yield history
        
        # Show thinking message
        history = history + [{"role": "assistant", "content": "🤔 Thinking..."}]
        yield history
        
        # Run the async processing with streaming
        async def async_gen():
            async for update in self._process_message_async_streaming(message, history[:-1]):  # Remove thinking message
                yield update
        
        # Create async generator and yield updates
        gen = async_gen()
        while True:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                update = loop.run_until_complete(gen.__anext__())
                yield update
                loop.close()
            except StopAsyncIteration:
                break
            except Exception as e:
                print(f"Error in process_message: {e}")
                # Remove thinking message and show error
                history_no_thinking = history[:-1]
                yield history_no_thinking + [{"role": "assistant", "content": f"❌ Error: {str(e)}"}]
                break
    
    async def _process_message_async_streaming(self, query: str, history: List[Dict[str, Any]]):
        """Async streaming message processing using Anthropic's native MCP"""
        
        # Build conversation messages
        messages = []
        
        # Add conversation history (filter out tool status messages)
        for msg in history:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role in ["user", "assistant"] and content:
                # Skip tool status/debug messages
                if role == "assistant" and any(
                    content.startswith(prefix) for prefix in ["🔧", "⏳", "✅", "❌", "💭", "🤔"]
                ):
                    continue
                messages.append({"role": role, "content": content})
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        print(f"Sending query to Claude with native MCP: {query}")
        
        try:
            # Show connecting message
            yield history + [{"role": "assistant", "content": "🔗 Connecting to tools..."}]
            await asyncio.sleep(0.1)
            
            # Use Anthropic's native MCP support with URL
            response = await self.client.beta.messages.create(
                model=MODEL_ID,
                max_tokens=4096,
                messages=messages,
                mcp_servers=[
                    {
                        "type": "url",
                        "url": f"{self.server_url}/sse",
                        "name": "oxenstierna-server",
                    }
                ],
                betas=["mcp-client-2025-04-04"]
            )
            
            # Show processing message
            yield history + [{"role": "assistant", "content": "⚡ Processing with Claude..."}]
            await asyncio.sleep(0.1)
            
            # Extract and show content with tool information
            content = ""
            tool_calls_found = False
            
            for block in response.content:
                if hasattr(block, 'type'):
                    if block.type == 'text' and hasattr(block, 'text'):
                        content += block.text
                    elif block.type == 'mcp_tool_use':
                        tool_calls_found = True
                        # Show tool usage
                        tool_msg = f"🔧 Using tool: **{block.name}** from {block.server_name}"
                        yield history + [{"role": "assistant", "content": tool_msg}]
                        await asyncio.sleep(0.1)
                        
                        # Show parameters
                        if hasattr(block, 'input') and block.input:
                            params_msg = f"📝 Parameters: ```json\n{json.dumps(block.input, indent=2)}\n```"
                            yield history + [{"role": "assistant", "content": params_msg}]
                            await asyncio.sleep(0.1)
                    elif block.type == 'mcp_tool_result':
                        # Show tool result
                        if hasattr(block, 'is_error') and not block.is_error:
                            result_msg = "✅ Tool executed successfully"
                        else:
                            result_msg = "❌ Tool execution failed"
                        yield history + [{"role": "assistant", "content": result_msg}]
                        await asyncio.sleep(0.1)
                elif hasattr(block, 'text'):
                    content += block.text
                elif hasattr(block, 'content'):
                    content += str(block.content)
            
            if not content.strip():
                if tool_calls_found:
                    content = "I've successfully used the available tools to process your request."
                else:
                    content = "I've processed your request."
            
            # Show final response
            yield history + [{"role": "assistant", "content": content}]
            
        except Exception as e:
            print(f"Full error details: {e}")
            print(f"Server URL attempted: {self.server_url}/sse")
            
            # More detailed error message for user
            detailed_msg = f"""❌ MCP Connection Error: {str(e)}

Troubleshooting steps:
1. Make sure the HTTP server is running: `python server.py --http`
2. Check server logs for errors
3. Verify server is accessible at: {self.server_url}/sse
4. Try: `curl {self.server_url}/sse` in terminal"""
            
            yield history + [{"role": "assistant", "content": detailed_msg}]
    
    async def _process_message_async(self, query: str, history: List[Dict[str, Any]]):
        """Legacy async processing (kept for compatibility)"""
        async for result in self._process_message_async_streaming(query, history):
            pass  # Just get the final result
        return result

# Create global client instance
client = MCPClientWrapper()

def create_interface():
    """Create the Gradio interface"""
    
    with gr.Blocks(title="MCP Client with Claude (Native)", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🤖 MCP Client with Claude (Native MCP Support)")
        gr.Markdown("Using Anthropic's native MCP client support")
        
        with gr.Row(equal_height=True):
            with gr.Column(scale=4):
                server_info = gr.Textbox(
                    label="MCP Server URL",
                    placeholder="Make sure to start server with: python server.py --http",
                    value="http://localhost:8000",
                    interactive=False
                )
            with gr.Column(scale=1):
                connect_btn = gr.Button("Connect", variant="primary")
        
        status = gr.Textbox(
            label="Connection Status", 
            interactive=False,
            show_label=True
        )
        
        gr.Markdown("### 💬 Chat Interface")
        
        chatbot = gr.Chatbot(
            value=[], 
            height=500,
            type="messages",
            show_copy_button=True
        )
        
        msg = gr.Textbox(
            label="Your Message",
            placeholder="Type your message here... (Press Enter to send)",
            lines=1,
            max_lines=4
        )
        
        with gr.Row():
            submit_btn = gr.Button("Send", variant="primary")
            clear_btn = gr.Button("Clear Chat")
        
        gr.Markdown("### ℹ️ Information")
        with gr.Accordion("Settings & Help", open=False):
            gr.Markdown(f"""
            **Claude Settings:**
            - Model: `{MODEL_ID}`
            - Using Anthropic's native MCP client support
            
            **Available MCP Tools:**
            - HTR (Handwritten Text Recognition) tools for processing historical documents
            - Search tools for Swedish National Archives records  
            - IIIF tools for accessing historical document images and metadata
            
            **Tips:**
            - Connect to the Oxenstierna MCP server first
            - Claude will automatically discover and use available tools
            - No manual tool schema conversion needed
            """)
        
        # Event handlers
        connect_btn.click(
            fn=client.connect,
            inputs=server_info,
            outputs=status
        )
        
        # Message submission
        msg.submit(
            fn=client.process_message,
            inputs=[msg, chatbot],
            outputs=chatbot,
        ).then(
            fn=lambda: "",
            outputs=msg
        )
        
        submit_btn.click(
            fn=client.process_message,
            inputs=[msg, chatbot],
            outputs=chatbot,
        ).then(
            fn=lambda: "",
            outputs=msg
        )
        
        clear_btn.click(lambda: ([], ""), outputs=[chatbot, msg])
        
    return demo

if __name__ == "__main__":
    # Check environment
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Warning: ANTHROPIC_API_KEY not set. Please set your Anthropic API key.")
    
    # Launch interface
    interface = create_interface()
    interface.queue()
    interface.launch(
        debug=True,
        share=False,
        server_name="0.0.0.0",
        server_port=7860
    )