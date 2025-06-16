import json
import asyncio
import os
from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Any, List, Dict, Union
from contextlib import AsyncExitStack
import gradio as gr
import time
import threading

# Optional: Phoenix tracing
try:
    from phoenix.otel import register
    tracer_provider = register(auto_instrument=True, endpoint="http://localhost:6006/v1/traces")
except ImportError:
    print("Phoenix tracing not available. Continuing without it.")

# vLLM Configuration
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://vllm-qwen3-32b-service.models:8005/v1")
MODEL_ID = os.getenv("MODEL_ID", "Qwen/Qwen3-32B")

# System prompt
SYSTEM_PROMPT = """You are a helpful assistant capable of accessing external functions and engaging in casual chat. Use the responses from these function calls to provide accurate and informative answers. The answers should be natural and hide the fact that you are using tools to access real-time information. Guide the user about available tools and their capabilities. Always utilize tools to access real-time information when required. Engage in a friendly manner to enhance the chat experience.

# Tools

{tools}

# Notes 

- Ensure responses are based on the latest information available from function calls.
- Maintain an engaging, supportive, and friendly tone throughout the dialogue.
- Always highlight the potential of available tools to assist users comprehensively."""

class MCPClientWrapper:
    """Wrapper class to manage MCP connections and message processing for Gradio"""
    
    def __init__(self):
        self.session = None
        self.exit_stack = None
        self.tools = {}
        self.client = AsyncOpenAI(
            api_key="EMPTY",
            base_url=VLLM_BASE_URL
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
            
            # Convert tools to format for LLM
            self.tools = {
                tool.name: {
                    "name": tool.name,
                    "callable": self._create_tool_callable(tool.name),
                    "schema": {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema or {"type": "object", "properties": {}},
                        },
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
        """Async message processing with streaming support"""
        # Build conversation messages for LLM
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT.format(
                    tools="\n- ".join(
                        [
                            f"{t['name']}: {t['schema']['function']['description']}"
                            for t in self.tools.values()
                        ]
                    )
                ),
            }
        ]
        
        # Add conversation history (filter out tool status messages)
        for msg in history:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role in ["user", "assistant"] and content:
                # Skip tool status messages but keep regular assistant messages
                if role == "assistant" and any(
                    content.startswith(prefix) for prefix in ["🔧", "⏳", "✅", "❌", "💭", "🔄", "📊"]
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
        
        # Show processing status
        history = history + [{"role": "assistant", "content": "🔄 Processing your request..."}]
        yield history
        
        # Query LLM with tools (streaming)
        print(f"Sending query to LLM: {query}")
        try:
            stream = await self.client.chat.completions.create(
                model=MODEL_ID,
                messages=messages,
                tools=([t["schema"] for t in self.tools.values()] if len(self.tools) > 0 else None),
                tool_choice="auto" if len(self.tools) > 0 else None,
                temperature=0,
                stream=True  # Enable streaming
            )
            
            # Remove processing message
            history = history[:-1]
            
            # Variables to accumulate the streamed response
            accumulated_content = ""
            accumulated_tool_calls = []
            current_tool_call = None
            finish_reason = None
            tool_decision_made = False
            
            # Add placeholder for assistant response
            assistant_message_index = len(history)
            history = history + [{"role": "assistant", "content": ""}]
            
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue
                
                # Check finish reason
                if chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason
                
                # Handle content streaming
                if delta.content:
                    accumulated_content += delta.content
                    history[assistant_message_index]["content"] = accumulated_content
                    yield history
                
                # Handle tool calls
                if delta.tool_calls:
                    # Show tool decision notification once
                    if not tool_decision_made:
                        tool_decision_made = True
                        if accumulated_content.strip():
                            # Keep any initial content
                            yield history
                        else:
                            # Remove empty content placeholder
                            history = history[:-1]
                        
                        history = history + [{"role": "assistant", "content": "🔄 Analyzing which tools to use..."}]
                        yield history
                    
                    for tool_call_delta in delta.tool_calls:
                        if tool_call_delta.index is not None:
                            # New tool call or continuing existing one
                            index = tool_call_delta.index
                            
                            # Ensure we have enough tool calls in the list
                            while len(accumulated_tool_calls) <= index:
                                accumulated_tool_calls.append({
                                    "id": None,
                                    "type": "function",
                                    "function": {
                                        "name": None,
                                        "arguments": ""
                                    }
                                })
                            
                            current_tool_call = accumulated_tool_calls[index]
                            
                            # Update tool call info
                            if tool_call_delta.id:
                                current_tool_call["id"] = tool_call_delta.id
                            
                            if tool_call_delta.function:
                                if tool_call_delta.function.name:
                                    current_tool_call["function"]["name"] = tool_call_delta.function.name
                                    # Update status to show which tool is being prepared
                                    history[-1]["content"] = f"🔄 Preparing to use tool: **{tool_call_delta.function.name}**"
                                    yield history
                                    
                                if tool_call_delta.function.arguments:
                                    current_tool_call["function"]["arguments"] += tool_call_delta.function.arguments
            
        except Exception as e:
            history[-1]["content"] = f"❌ LLM Error: {str(e)}"
            yield history
            return
        
        print(f"LLM Response - finish_reason: {finish_reason}")
        print(f"Tool calls accumulated: {len(accumulated_tool_calls)}")
        
        # Process tool calls if any
        if finish_reason == "tool_calls" and accumulated_tool_calls:
            # Remove the "Analyzing which tools to use..." message
            if history and history[-1]["content"].startswith("🔄"):
                history = history[:-1]
            
            # Process each tool call and collect results
            tool_results = []
            total_tools = len([tc for tc in accumulated_tool_calls if tc["function"]["name"]])
            tool_count = 0
            
            for tool_call in accumulated_tool_calls:
                if not tool_call["function"]["name"]:
                    continue
                
                tool_count += 1
                tool_name = tool_call['function']['name']
                
                try:
                    arguments = json.loads(tool_call["function"]["arguments"])
                except:
                    arguments = {}
                
                # Show detailed tool execution status
                history = history + [{
                    "role": "assistant", 
                    "content": f"🔧 **Tool {tool_count}/{total_tools}: {tool_name}**\n\n📥 **Input parameters:**"
                }]
                yield history
                
                # Show parameters in a more readable format
                if arguments:
                    params_lines = []
                    for key, value in arguments.items():
                        if isinstance(value, (dict, list)):
                            value_str = json.dumps(value, indent=2)
                        else:
                            value_str = str(value)
                        params_lines.append(f"• **{key}**: {value_str}")
                    
                    params_content = "\n".join(params_lines)
                else:
                    params_content = "• No parameters required"
                
                history = history + [{"role": "assistant", "content": params_content}]
                yield history
                
                # Execute tool with live status
                history = history + [{"role": "assistant", "content": f"⏳ Executing **{tool_name}**..."}]
                yield history
                
                start_time = time.time()
                try:
                    tool_result = await self.tools[tool_name]["callable"](**arguments)
                    exec_time = time.time() - start_time
                    
                    # Remove executing message and show completion
                    history = history[:-1]
                    history = history + [{
                        "role": "assistant", 
                        "content": f"✅ **{tool_name}** completed in {exec_time:.2f}s"
                    }]
                    yield history
                    
                    # Show result preview
                    history = history + [{"role": "assistant", "content": "📊 **Result:**"}]
                    yield history
                    
                    # Format result nicely
                    try:
                        result_json = json.loads(tool_result)
                        if isinstance(result_json, dict) and len(result_json) <= 5:
                            # For small objects, show inline
                            result_lines = []
                            for key, value in result_json.items():
                                result_lines.append(f"• **{key}**: {value}")
                            result_content = "\n".join(result_lines)
                        else:
                            # For larger results, use code block
                            result_content = "```json\n" + json.dumps(result_json, indent=2)[:1000] + "\n```"
                    except:
                        # For non-JSON results
                        result_preview = str(tool_result)[:500]
                        if len(str(tool_result)) > 500:
                            result_preview += "... (truncated)"
                        result_content = f"```\n{result_preview}\n```"
                    
                    history = history + [{"role": "assistant", "content": result_content}]
                    yield history
                    
                    # Add separator between tools
                    if tool_count < total_tools:
                        history = history + [{"role": "assistant", "content": "---"}]
                        yield history
                    
                    # Store result for final LLM call
                    tool_results.append({
                        "tool_call_id": tool_call["id"],
                        "content": str(tool_result)
                    })
                    
                except Exception as e:
                    # Remove executing message and show error
                    history = history[:-1]
                    history = history + [{
                        "role": "assistant", 
                        "content": f"❌ **{tool_name}** failed: {str(e)}"
                    }]
                    yield history
                    
                    # Store error result
                    tool_results.append({
                        "tool_call_id": tool_call["id"],
                        "content": f"Error: {str(e)}"
                    })
            
            # After all tool calls, prepare messages for final response
            messages.append({
                "role": "assistant",
                "content": accumulated_content or "",
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": tc["type"],
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"]
                        }
                    }
                    for tc in accumulated_tool_calls
                    if tc["function"]["name"]
                ]
            })
            
            # Add all tool results
            for result in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": result["tool_call_id"],
                    "content": result["content"]
                })
            
            # Get final response after tool execution (also streaming)
            history = history + [{"role": "assistant", "content": "💭 Analyzing results and preparing response..."}]
            yield history
            
            try:
                final_stream = await self.client.chat.completions.create(
                    model=MODEL_ID,
                    messages=messages,
                    temperature=0,
                    stream=True  # Stream the final response too
                )
                
                # Remove processing message
                history = history[:-1]
                
                # Add separator before final response
                history = history + [{"role": "assistant", "content": "---\n\n**📝 Final Response:**"}]
                yield history
                
                # Add placeholder for final response
                final_message_index = len(history)
                history = history + [{"role": "assistant", "content": ""}]
                final_content = ""
                
                async for chunk in final_stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta and delta.content:
                        final_content += delta.content
                        history[final_message_index]["content"] = final_content
                        yield history
                
                # If no content was generated
                if not final_content:
                    history[final_message_index]["content"] = "I've successfully processed the tool results. The information has been gathered as requested."
                    yield history
                    
            except Exception as e:
                # Remove processing message if still there
                if history and history[-1]["content"].startswith("💭"):
                    history = history[:-1]
                history = history + [{"role": "assistant", "content": f"❌ Error generating final response: {str(e)}"}]
                yield history
            
        else:
            # No tools used, content was already streamed
            if not accumulated_content:
                history[assistant_message_index]["content"] = "I understand your request. How can I help you today?"
                yield history

# Create global client instance
client = MCPClientWrapper()


def create_interface():
    """Create the Gradio interface"""
    
    with gr.Blocks(title="Oxenstierna", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# Oxenstierna 🐂⭐")

    
        gr.Markdown("### ⚙️ Settings")
        with gr.Accordion("Settings & Help", open=False):
            gr.Markdown(f"""
            **vLLM Settings:**
            - Base URL: `{VLLM_BASE_URL}`
            - Model: `{MODEL_ID}`
            """)
            
            with gr.Row(equal_height=True):
                with gr.Column(scale=4):
                    server_path = gr.Textbox(
                        label="MCP Server Path",
                        placeholder="Enter path to server script (e.g., simple_mcp_server.py)",
                        value="simple_mcp_server.py"
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
            height=600,
            type="messages",
            show_copy_button=True,
            bubble_full_width=False
        )
        with gr.Row():

            msg = gr.Textbox(
                label="Your Message",
                placeholder="Type your message here... (Press Enter to send)",
                lines=1,
                max_lines=4
            )
            submit_btn = gr.Button("Send", variant="primary",  scale=0)
            clear_btn = gr.Button("Clear Chat",  scale=0)
    
        
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
    if not os.getenv("VLLM_BASE_URL"):
        print("Info: VLLM_BASE_URL not set. Using default: http://vllm-qwen3-32b-service.models:8005/v1")
    
    # Launch interface
    interface = create_interface()
    interface.queue()
    interface.launch(
        debug=True,
        share=False,
        server_name="0.0.0.0",
        server_port=7860
    )
