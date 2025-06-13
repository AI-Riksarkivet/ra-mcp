import json
import asyncio
import os
from anthropic import AsyncAnthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Any, List, Dict, Union
from contextlib import AsyncExitStack
import gradio as gr
import time
import threading

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

# Optional: Phoenix tracing
try:
    from phoenix.otel import register
    tracer_provider = register(auto_instrument=True, endpoint="http://localhost:6006/v1/traces")
except ImportError:
    print("Phoenix tracing not available. Continuing without it.")

# Anthropic Configuration
MODEL_ID = os.getenv("MODEL_ID", "claude-sonnet-4-20250514")

# System prompt
SYSTEM_PROMPT = """You are a helpful assistant for the Oxenstierna historical document processing system. You have access to specialized tools for working with Swedish National Archives materials through MCP (Model Context Protocol).

# Available Tools

{tools}

# Tool Categories & Workflow

**🔍 Search Tools** - Find historical documents:
- Use search tools to find documents in the Swedish National Archives
- Get PIDs (document identifiers) for further processing

**🖼️ IIIF Tools** - Access digitized images:
- Use PIDs from search results to access document collections and image batches
- Download specific images or get IIIF URLs for viewing
- Access metadata and technical details about digitized documents

**✍️ HTR Tools** - Extract handwritten text:
- Process images to extract handwritten text using specialized Swedish models
- Support multiple output formats (text, ALTO XML, PAGE XML, JSON)
- Handle different document types (letters, spreads, English/Swedish)

# Instructions

- **Extract search terms**: When users ask about searching for something, ALWAYS extract the key terms and use them as the 'text' parameter in search tools
- **Show your reasoning**: Always explain your thought process step by step
- **Suggest workflows**: Help users understand how to combine tools effectively
- **Explain next steps**: After each tool use, suggest what the user might want to do next
- **Be educational**: Explain what each tool does and why it's useful for historical research
- **Handle errors gracefully**: If a tool fails, explain what went wrong and suggest alternatives

# Parameter Guidelines

**For search tools:**
- ALWAYS provide the 'text' parameter with relevant search terms from the user's question
- Example: "vad finns det om häxor?" → use text="häxor"
- Example: "search for Nobel" → use text="Nobel"
- Example: "Stockholm documents" → use text="Stockholm"

# Typical Workflows

1. **Find & Transcribe**: Search → Get PID → Access images → Process with HTR
2. **Browse Collection**: Search → Get collection info → Browse manifests → Download images
3. **Batch Processing**: Search → Get all images from PID → Process multiple images with HTR

Always think step by step and guide users through these powerful historical document tools."""

class MCPClientWrapper:
    """Wrapper class to manage MCP connections and message processing for Gradio"""
    
    def __init__(self):
        self.session = None
        self.exit_stack = None
        self.tools = {}
        self.client = AsyncAnthropic(
            api_key=anthropic_api_key
        )
        # Create a persistent event loop in a separate thread
        self.loop = None
        self.loop_thread = None
        self._start_event_loop()
    
    def _start_event_loop(self):
        """Start event loop in a separate thread"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
        # Wait for loop to be ready
        time.sleep(0.1)
    
    def _run_async(self, coro):
        """Run async function in the persistent event loop"""
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()
    
    def connect(self, server_path: str):
        """Connect to MCP server"""
        return self._run_async(self._connect(server_path))
    
    async def _connect(self, server_path: str):
        """Establishes connection to MCP server"""
        # Clean up existing connection if any
        if self.exit_stack:
            await self.exit_stack.aclose()
        
        self.exit_stack = AsyncExitStack()
        
        # Determine if Python or Node server
        is_python = server_path.endswith('.py')
        command = "python" if is_python else "node"
        
        # Server parameters
        server_params = StdioServerParameters(
            command=command,
            args=[server_path],
            env={"PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"} if is_python else None,
        )
        
        try:
            # Connect to MCP server
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.read, self.write = stdio_transport
            
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.read, self.write)
            )
            await self.session.initialize()
            
            # Get available tools
            mcp_tools = await self.session.list_tools()
            
            # Convert tools to format for Anthropic
            self.tools = {
                tool.name: {
                    "name": tool.name,
                    "callable": self._create_tool_callable(tool.name),
                    "schema": {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema or {"type": "object", "properties": {}},
                    },
                }
                for tool in mcp_tools.tools
            }
            
            tool_names = list(self.tools.keys())
            return f"✅ Connected to MCP server. Available tools: {', '.join(tool_names)}"
            
        except Exception as e:
            return f"❌ Failed to connect: {str(e)}"
    
    def _create_tool_callable(self, tool_name: str):
        """Create a callable function for a specific tool"""
        async def callable(*args, **kwargs):
            if not self.session:
                raise RuntimeError("Not connected to MCP server")
            response = await self.session.call_tool(tool_name, arguments=kwargs)
            return response.content[0].text if not response.isError else f"Error: {response.content[0].text}"
        return callable
    
    def process_message(self, message: str, history: List[Dict[str, Any]]):
        """Process message and yield updates synchronously"""
        if not message.strip():
            yield history
            return
            
        if not self.session:
            yield history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": "❌ Please connect to an MCP server first."}
            ]
            return
        
        # Run the async generator and yield results
        async def async_gen():
            async for update in self._process_message_async(message, history):
                yield update
        
        # Create async generator
        gen = async_gen()
        
        # Yield each update
        while True:
            try:
                update = self._run_async(gen.__anext__())
                yield update
            except StopAsyncIteration:
                break
            except Exception as e:
                print(f"Error in process_message: {e}")
                yield history + [{"role": "assistant", "content": f"❌ Error: {str(e)}"}]
                break
    
    async def _process_message_async(self, query: str, history: List[Dict[str, Any]]):
        """Async message processing"""
        # Build system prompt for Claude
        system_prompt = SYSTEM_PROMPT.format(
            tools="\n- ".join(
                [
                    f"{t['name']}: {t['schema']['description']}"
                    for t in self.tools.values()
                ]
            )
        )
        
        # Build conversation messages for Claude (no system role in messages)
        messages = []
        
        # Add conversation history (filter out tool status messages)
        for msg in history:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role in ["user", "assistant"] and content:
                # Skip tool status messages but keep regular assistant messages
                if role == "assistant" and any(
                    content.startswith(prefix) for prefix in ["🔧", "⏳", "✅", "❌", "💭"]
                ):
                    continue
                # Skip code blocks from tool results
                if role == "assistant" and content.startswith("```") and content.endswith("```"):
                    continue
                messages.append({"role": role, "content": content})
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        # Update history with user message
        history = history + [{"role": "user", "content": query}]
        yield history
        
        # Query Claude with tools (streaming)
        print(f"Sending query to Claude: {query}")
        
        # Debug: Print tool schemas being sent to Claude
        if self.tools:
            print("=== TOOL SCHEMAS SENT TO CLAUDE ===")
            for tool_name, tool_data in self.tools.items():
                print(f"Tool: {tool_name}")
                print(f"Schema: {json.dumps(tool_data['schema'], indent=2)}")
                print("---")
        
        try:
            stream = await self.client.messages.create(
                model=MODEL_ID,
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=([t["schema"] for t in self.tools.values()] if len(self.tools) > 0 else None),
                temperature=0,
                stream=True,
            )
        except Exception as e:
            history = history + [{"role": "assistant", "content": f"❌ Claude Error: {str(e)}"}]
            yield history
            return
        
        # Process streaming response
        current_content = ""
        tool_uses = []
        stop_reason = None
        
        assistant_message_started = False
        
        async for chunk in stream:
            if chunk.type == "message_start":
                continue
            elif chunk.type == "message_delta":
                if chunk.delta.stop_reason:
                    stop_reason = chunk.delta.stop_reason
            elif chunk.type == "content_block_start":
                if chunk.content_block.type == "text":
                    if not assistant_message_started:
                        # Start new assistant message
                        history = history + [{"role": "assistant", "content": ""}]
                        assistant_message_started = True
                        yield history
                elif chunk.content_block.type == "tool_use":
                    tool_uses.append(chunk.content_block)
            elif chunk.type == "content_block_delta":
                if chunk.delta.type == "text_delta":
                    current_content += chunk.delta.text
                    # Update the last assistant message with streaming content
                    if history and history[-1]["role"] == "assistant":
                        history[-1]["content"] = current_content
                        yield history
            elif chunk.type == "message_stop":
                break
        
        print(f"Claude Response - stop_reason: {stop_reason}")
        print(f"Tool uses: {tool_uses}")
        
        # Check for tool use
        if tool_uses:
            # Process each tool use and collect results
            tool_results = []
            for tool_use in tool_uses:
                arguments = tool_use.input
                
                # Show tool being used
                history = history + [{
                    "role": "assistant", 
                    "content": f"🔧 Using tool: **{tool_use.name}**"
                }]
                yield history
                
                # Show parameters
                params_content = "```json\n" + json.dumps(arguments, indent=2) + "\n```"
                history = history + [{"role": "assistant", "content": params_content}]
                yield history
                
                # Execute tool
                history = history + [{"role": "assistant", "content": "⏳ Executing..."}]
                yield history
                await asyncio.sleep(0.1)  # Small delay to ensure UI updates
                
                start_time = time.time()
                try:
                    tool_result = await self.tools[tool_use.name]["callable"](**arguments)
                    exec_time = time.time() - start_time
                    
                    # Remove executing message and show completion
                    history = history[:-1]  # Remove "Executing..."
                    history = history + [{
                        "role": "assistant", 
                        "content": f"✅ Completed in {exec_time:.2f}s"
                    }]
                    yield history
                    
                    # Show result
                    try:
                        result_json = json.loads(tool_result)
                        result_content = "```json\n" + json.dumps(result_json, indent=2) + "\n```"
                    except Exception:
                        result_content = "```\n" + str(tool_result)[:1000] + "\n```"  # Limit length
                    
                    history = history + [{"role": "assistant", "content": result_content}]
                    yield history
                    
                    # Store result for final Claude call
                    tool_results.append({
                        "tool_use_id": tool_use.id,
                        "content": str(tool_result)
                    })
                    
                except Exception as e:
                    # Remove executing message and show error
                    history = history[:-1]  # Remove "Executing..."
                    history = history + [{
                        "role": "assistant", 
                        "content": f"❌ Error: {str(e)}"
                    }]
                    yield history
                    
                    # Store error result
                    tool_results.append({
                        "tool_use_id": tool_use.id,
                        "content": f"Error: {str(e)}"
                    })
            
            # After all tool uses, prepare messages for final response
            # Create content array with both text and tool_use blocks
            assistant_content = []
            if current_content.strip():
                assistant_content.append({
                    "type": "text",
                    "text": current_content
                })
            
            # Add tool uses
            for tool_use in tool_uses:
                assistant_content.append({
                    "type": "tool_use",
                    "id": tool_use.id,
                    "name": tool_use.name,
                    "input": tool_use.input
                })
            
            messages.append({
                "role": "assistant",
                "content": assistant_content
            })
            
            # Add all tool results
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": result["tool_use_id"],
                    "content": result["content"]
                } for result in tool_results]
            })
            
            # Get final response after tool execution (streaming)
            history = history + [{"role": "assistant", "content": "💭 Processing results..."}]
            yield history
            
            try:
                final_stream = await self.client.messages.create(
                    model=MODEL_ID,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=messages,
                    temperature=0,
                    stream=True,
                )
                
                # Remove processing message
                history = history[:-1]
                
                # Stream final response
                final_content = ""
                final_assistant_started = False
                
                async for chunk in final_stream:
                    if chunk.type == "content_block_start" and chunk.content_block.type == "text":
                        if not final_assistant_started:
                            history = history + [{"role": "assistant", "content": ""}]
                            final_assistant_started = True
                            yield history
                    elif chunk.type == "content_block_delta" and chunk.delta.type == "text_delta":
                        final_content += chunk.delta.text
                        if history and history[-1]["role"] == "assistant":
                            history[-1]["content"] = final_content
                            yield history
                    elif chunk.type == "message_stop":
                        break
                
                if not final_content.strip():
                    history = history + [{"role": "assistant", "content": "I've processed the tool results successfully."}]
                    yield history
                    
            except Exception as e:
                # Remove processing message if still there
                if history and history[-1]["content"] == "💭 Processing results...":
                    history = history[:-1]
                history = history + [{"role": "assistant", "content": f"❌ Error getting final response: {str(e)}"}]
                yield history
            
        else:
            # No tools used, response already streamed
            if not current_content.strip():
                history = history + [{"role": "assistant", "content": "I understand your request but received an empty response."}]
                yield history

# Create global client instance
client = MCPClientWrapper()

def create_interface():
    """Create the Gradio interface"""
    
    with gr.Blocks(title="MCP Client with Claude", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🤖 MCP Client with Claude")
        gr.Markdown("Connect to your MCP server and interact with tools using Claude")
        
        with gr.Row(equal_height=True):
            with gr.Column(scale=4):
                server_path = gr.Textbox(
                    label="MCP Server Path",
                    placeholder="Enter path to server script (e.g., ../src/oxenstierna/server.py)",
                    value="../src/oxenstierna/server.py"
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
            show_copy_button=True,
            bubble_full_width=False
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
            
            **Available MCP Tools:**
            - HTR (Handwritten Text Recognition) tools for processing historical documents
            - Search tools for Swedish National Archives records  
            - IIIF tools for accessing historical document images and metadata
            
            **Tips:**
            - Connect to the Oxenstierna MCP server first
            - The assistant will automatically use available tools
            - Tool executions are shown in real-time
            - Claude will show its reasoning process and thought process
            """)
        
        # Event handlers
        connect_btn.click(
            fn=client.connect,
            inputs=server_path,
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