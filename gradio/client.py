import asyncio
import os
import json
from typing import List, Dict, Any, Union

import gradio as gr
from gradio.components.chatbot import ChatMessage
from anthropic import Anthropic
from smolagents import MCPClient


class MCPClientWrapper:
    def __init__(self):
        self.mcp_client = None
        self.anthropic = None
        self.tools = []
        self.api_key = None
        self.current_server_url = None

    def set_api_key(self, api_key: str) -> str:
        """Set the Anthropic API key and initialize the client"""
        if not api_key or not api_key.strip():
            return "❌ Please provide a valid Anthropic API key"

        # Basic format validation
        api_key = api_key.strip()
        if not api_key.startswith("sk-ant-"):
            return "❌ Invalid API key format. Anthropic API keys should start with 'sk-ant-'"

        try:
            # Create client and test the key with a minimal request
            test_client = Anthropic(api_key=api_key)

            # Make a small test request to validate the key
            test_response = test_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Use consistent model name
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )

            self.api_key = api_key
            self.anthropic = test_client
            return "✅ Anthropic API key validated and set successfully"

        except Exception as e:
            error_msg = str(e)
            if "authentication_error" in error_msg or "invalid x-api-key" in error_msg:
                return "❌ Invalid API key. Please check your key at https://console.anthropic.com/"
            elif "insufficient_quota" in error_msg:
                return "❌ API key valid but insufficient quota. Please check your billing at https://console.anthropic.com/"
            else:
                return f"❌ Error validating API key: {error_msg}"

    def connect(self, server_url: str) -> str:
        """Connect to MCP server via URL"""
        if not self.anthropic:
            return "❌ Please set your Anthropic API key first"

        if not server_url or not server_url.strip():
            return "❌ Please provide a valid server URL"

        try:
            # Disconnect from previous server if connected
            if self.mcp_client:
                try:
                    self.mcp_client.disconnect()
                except:
                    pass  # Ignore errors during disconnect

            # Connect to new server
            server_url = server_url.strip()
            self.mcp_client = MCPClient({"url": server_url})
            self.tools = self.mcp_client.get_tools()
            self.current_server_url = server_url

            tool_names = [
                tool.name if hasattr(tool, "name") else str(tool) for tool in self.tools
            ]
            return f"✅ Connected to MCP server at {server_url}. Available tools: {', '.join(tool_names)}"

        except Exception as e:
            return f"❌ Failed to connect to MCP server: {str(e)}"

    def disconnect(self):
        """Disconnect from current MCP server"""
        if self.mcp_client:
            try:
                self.mcp_client.disconnect()
            except:
                pass
            self.mcp_client = None
            self.tools = []
            self.current_server_url = None

    def _convert_mcp_tool_to_anthropic(self, tool) -> Dict[str, Any]:
        """Convert MCP tool to Anthropic API format"""
        tool_def = {
            "name": tool.name,
            "description": tool.description or f"Execute {tool.name} tool",
        }

        # Handle input schema - ensure it's proper JSON Schema
        if hasattr(tool, "input_schema") and tool.input_schema:
            input_schema = tool.input_schema
            # Ensure it has required JSON Schema fields
            if isinstance(input_schema, dict):
                if "type" not in input_schema:
                    input_schema["type"] = "object"
                if (
                    "properties" not in input_schema
                    and input_schema["type"] == "object"
                ):
                    input_schema["properties"] = {}
                tool_def["input_schema"] = input_schema
            else:
                # Fallback schema
                tool_def["input_schema"] = {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": True,
                }
        else:
            # Default schema for tools without input schema
            tool_def["input_schema"] = {
                "type": "object",
                "properties": {},
                "additionalProperties": True,
            }

        return tool_def

    def _ensure_message_alternation(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Ensure proper user/assistant alternation in messages"""
        if not messages:
            return messages

        fixed_messages = []
        last_role = None

        for msg in messages:
            current_role = msg.get("role")
            if current_role == last_role:
                # Skip duplicate consecutive roles
                continue
            if current_role in ["user", "assistant"]:
                fixed_messages.append(msg)
                last_role = current_role

        # Ensure it starts with user message
        if fixed_messages and fixed_messages[0]["role"] != "user":
            fixed_messages = fixed_messages[1:]

        return fixed_messages

    def process_message(
        self, message: str, history: List[Union[Dict[str, Any], ChatMessage]]
    ) -> tuple:
        if not self.anthropic:
            return history + [
                {"role": "user", "content": message},
                {
                    "role": "assistant",
                    "content": "❌ Please set your Anthropic API key first.",
                },
            ], gr.Textbox(value="")

        if not self.mcp_client:
            return history + [
                {"role": "user", "content": message},
                {
                    "role": "assistant",
                    "content": "❌ Please connect to an MCP server first.",
                },
            ], gr.Textbox(value="")

        try:
            # Convert history to Claude format - only include text messages for API
            claude_messages = []
            for msg in history:
                if isinstance(msg, ChatMessage):
                    role, content = msg.role, msg.content
                else:
                    role, content = msg.get("role"), msg.get("content")

                # Only include user/assistant messages, skip metadata-heavy messages
                if (
                    role in ["user", "assistant"]
                    and content
                    and not content.startswith("I'll use the")
                ):
                    # Skip tool execution messages
                    if not (isinstance(msg, dict) and msg.get("metadata")):
                        claude_messages.append({"role": role, "content": content})

            # Add current user message
            claude_messages.append({"role": "user", "content": message})

            # Ensure proper message alternation
            claude_messages = self._ensure_message_alternation(claude_messages)

            # Convert tools to Claude format
            claude_tools = []
            if self.tools:
                for tool in self.tools:
                    if hasattr(tool, "name"):
                        try:
                            claude_tool = self._convert_mcp_tool_to_anthropic(tool)
                            claude_tools.append(claude_tool)
                        except Exception as e:
                            print(f"Warning: Failed to convert tool {tool.name}: {e}")

            print(f"Debug - Sending to API:")
            print(f"Messages: {json.dumps(claude_messages, indent=2)}")
            print(
                f"Tools: {json.dumps(claude_tools, indent=2) if claude_tools else 'None'}"
            )

            # Get response from Claude
            api_params = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 2000,
                "messages": claude_messages,
            }

            if claude_tools:
                api_params["tools"] = claude_tools

            response = self.anthropic.messages.create(**api_params)

            result_messages = []

            # Process response content
            for content in response.content:
                if content.type == "text":
                    result_messages.append(
                        {"role": "assistant", "content": content.text}
                    )

                elif content.type == "tool_use":
                    tool_name = content.name
                    tool_args = content.input
                    tool_use_id = content.id

                    result_messages.append(
                        {
                            "role": "assistant",
                            "content": f"I'll use the {tool_name} tool to help answer your question.",
                            "metadata": {
                                "title": f"Using tool: {tool_name}",
                                "log": f"Parameters: {json.dumps(tool_args, ensure_ascii=True)}",
                                "status": "pending",
                                "id": f"tool_call_{tool_name}",
                            },
                        }
                    )

                    # Execute tool using MCP client
                    try:
                        # Find the tool and execute it
                        target_tool = None
                        for tool in self.tools:
                            if hasattr(tool, "name") and tool.name == tool_name:
                                target_tool = tool
                                break

                        if target_tool:
                            result_content = target_tool(**tool_args)
                        else:
                            result_content = f"Tool {tool_name} not found"

                        # Format result content
                        if isinstance(result_content, (dict, list)):
                            formatted_result = json.dumps(result_content, indent=2)
                        else:
                            formatted_result = str(result_content)

                        result_messages.append(
                            {
                                "role": "assistant",
                                "content": f"```json\n{formatted_result}\n```",
                                "metadata": {
                                    "title": f"Tool Result for {tool_name}",
                                    "status": "done",
                                    "id": f"result_{tool_name}",
                                },
                            }
                        )

                        # Create proper tool result message for API
                        claude_messages.append(
                            {
                                "role": "assistant",
                                "content": [
                                    {
                                        "type": "tool_use",
                                        "id": tool_use_id,
                                        "name": tool_name,
                                        "input": tool_args,
                                    }
                                ],
                            }
                        )

                        claude_messages.append(
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": tool_use_id,
                                        "content": str(result_content),
                                    }
                                ],
                            }
                        )

                        # Get follow-up response from Claude with proper tool result format
                        follow_up_response = self.anthropic.messages.create(
                            model="claude-3-5-sonnet-20241022",
                            max_tokens=2000,
                            messages=claude_messages,
                            tools=claude_tools if claude_tools else None,
                        )

                        # Add follow-up response
                        for follow_content in follow_up_response.content:
                            if follow_content.type == "text":
                                result_messages.append(
                                    {
                                        "role": "assistant",
                                        "content": follow_content.text,
                                    }
                                )

                    except Exception as tool_error:
                        print(f"Tool execution error: {tool_error}")
                        result_messages.append(
                            {
                                "role": "assistant",
                                "content": f"❌ Error executing tool {tool_name}: {str(tool_error)}",
                                "metadata": {
                                    "title": "Tool Error",
                                    "status": "error",
                                    "id": f"error_{tool_name}",
                                },
                            }
                        )

            return history + [
                {"role": "user", "content": message}
            ] + result_messages, gr.Textbox(value="")

        except Exception as e:
            print(f"API Error: {e}")
            error_message = str(e)

            # Provide more specific error messages
            if "invalid_request_error" in error_message:
                if "tools" in error_message:
                    error_message = f"❌ Tool schema error: {error_message}"
                else:
                    error_message = f"❌ Invalid request format: {error_message}"
            elif "authentication_error" in error_message:
                error_message = "❌ Authentication failed. Please check your API key."

            return history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": error_message},
            ], gr.Textbox(value="")


client = MCPClientWrapper()


def gradio_interface():
    with gr.Blocks(title="MCP Client") as demo:
        gr.Markdown("# MCP Test Client")
        gr.Markdown("Connect to MCP server and chat with the assistant")

        # API Key Section
        gr.Markdown("## 🔑 Step 1: Set Your Anthropic API Key")
        gr.Markdown(
            "Get your API key from [console.anthropic.com](https://console.anthropic.com/)"
        )

        with gr.Row(equal_height=True):
            with gr.Column(scale=4):
                api_key_input = gr.Textbox(
                    label="Anthropic API Key",
                    placeholder="Enter your Anthropic API key (sk-ant-...)",
                    type="password",
                    value="",
                )
            with gr.Column(scale=1):
                set_key_btn = gr.Button("Set API Key", variant="primary")

        api_key_status = gr.Textbox(label="API Key Status", interactive=False)

        # Server Connection Section
        gr.Markdown("## 🔗 Step 2: Connect to MCP Server")

        with gr.Row(equal_height=True):
            with gr.Column(scale=4):
                server_url = gr.Textbox(
                    label="MCP Server URL",
                    placeholder="Enter MCP server URL (e.g., https://example.com/gradio_api/mcp/sse)",
                    value="https://gabriel-htrflow-mcp.hf.space/gradio_api/mcp/sse",
                )
            with gr.Column(scale=1):
                connect_btn = gr.Button("Connect", variant="primary")

        # Add some predefined server options
        gr.Markdown("### Quick Connect Options:")
        with gr.Row():
            gradio_mcp_btn = gr.Button("Gradio MCP Server", size="sm")
            # Add more predefined servers as needed

        connection_status = gr.Textbox(label="Connection Status", interactive=False)

        # Chat Section
        gr.Markdown("## 💬 Step 3: Chat with Assistant")

        chatbot = gr.Chatbot(
            value=[],
            height=500,
            type="messages",
            show_copy_button=True,
            avatar_images=("👤", "🤖"),
        )

        with gr.Row(equal_height=True):
            msg = gr.Textbox(
                label="Your Question",
                placeholder="Ask a question to test the MCP tools...",
                scale=4,
            )
            clear_btn = gr.Button("Clear Chat", scale=1)

        # Event handlers
        set_key_btn.click(
            client.set_api_key, inputs=api_key_input, outputs=api_key_status
        )
        connect_btn.click(client.connect, inputs=server_url, outputs=connection_status)

        # Quick connect buttons
        gradio_mcp_btn.click(
            lambda: "https://gabriel-htrflow-mcp.hf.space/gradio_api/mcp/sse",
            outputs=server_url,
        )

        msg.submit(client.process_message, [msg, chatbot], [chatbot, msg])
        clear_btn.click(lambda: [], None, chatbot)

    return demo


if __name__ == "__main__":
    interface = gradio_interface()
    try:
        interface.launch(debug=True)
    finally:
        client.disconnect()
