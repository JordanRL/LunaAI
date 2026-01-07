"""
Console output formatting for Luna system.

This adapter handles console output using Rich, implementing panels
for different types of content with left, center, and right alignments.
"""

import json
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.json import JSON
from rich.layout import Layout
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

from domain.models.console import ResponsivePanel


class DebugLevel(Enum):
    """Debug verbosity levels for Luna system."""

    NONE = 0  # No debug output
    MINIMAL = 1  # Only basic info (agent transitions, errors)
    STANDARD = 2  # Standard debug info (+ content snippets, stats)
    VERBOSE = 3  # Verbose output (+ complete content, tool details)
    TRACE = 4  # Full trace (+ all message content, exact routing)


class DebugSymbols:
    """Standard symbols for debug outputs to ensure consistency."""

    INFO = "ℹ️"
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    ROUTING = "🔄"
    MEMORY = "📝"
    TOOL = "🔧"
    METRIC = "📊"
    THINKING = "💭"
    PROCESSING = "⚙️"
    LOADING = "⏳"

    # Directional symbols
    DIRECTION_TO = "→"
    DIRECTION_FROM = "←"
    DIRECTION_BOTH = "⟷"


class ConsoleAdapter:
    """
    Console adapter for Luna that formats and displays various output types.
    Handles user messages, agent thinking, tools, and debug messages.
    """

    def __init__(self):
        """Initialize the console adapter."""
        self.console = Console()
        self.symbols = DebugSymbols()

        # Color mappings for different debug levels
        self.level_styles = {
            DebugLevel.MINIMAL: "bold cyan",
            DebugLevel.STANDARD: "bold green",
            DebugLevel.VERBOSE: "bold yellow",
            DebugLevel.TRACE: "bold magenta",
        }

        # Symbol styles
        self.symbol_styles = {
            self.symbols.INFO: "blue",
            self.symbols.SUCCESS: "green",
            self.symbols.WARNING: "yellow",
            self.symbols.ERROR: "red",
            self.symbols.ROUTING: "cyan",
            self.symbols.MEMORY: "green",
            self.symbols.TOOL: "yellow",
            self.symbols.METRIC: "blue",
            self.symbols.THINKING: "cyan",
            self.symbols.PROCESSING: "yellow",
            self.symbols.LOADING: "blue",
        }

        # Agent styles for visualization
        self.agent_styles = {
            "dispatcher": "blue",
            "memory_retrieval": "green",
            "emotion_processor": "magenta",
            "intent_analyzer": "yellow",
            "relationship_manager": "cyan",
            "self_reflection": "purple",
            "summarizer": "red",
            "outputter": "bright_blue",
            # Default for other agents
            "default": "white",
        }

    def get_agent_style(self, agent_name: str) -> str:
        """
        Get the style for a specific agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Style string for the agent
        """
        # Convert to lowercase for consistent matching
        agent_lower = agent_name.lower()

        # Check if we have a specific style for this agent
        for key in self.agent_styles:
            if key in agent_lower:
                return self.agent_styles[key]

        # Default style
        return self.agent_styles["default"]

    def format_content_for_display(
        self, content: str, max_width: int = 80
    ) -> Union[Markdown, Text]:
        """
        Format content for display, using Markdown if appropriate.

        Args:
            content: Content to format
            max_width: Maximum width for wrapping

        Returns:
            Formatted content as Markdown or Text
        """
        # Check if content has markdown indicators
        return Markdown(content)

    def truncate_content(self, content: str, max_length: int = 100) -> str:
        """
        Smartly truncate content for display.

        Args:
            content: Content to truncate
            max_length: Maximum length before truncation

        Returns:
            Truncated content
        """
        if not content:
            return "<empty>"

        # Handle standard string content
        if len(content) <= max_length:
            return content

        # Truncate and format
        return content[:max_length].rstrip() + "..."

    def clear(self) -> None:
        """Clear the console."""
        self.console.clear()

    # Debug message formatting and display
    def format_debug_message(
        self,
        message: str,
        level: DebugLevel = DebugLevel.STANDARD,
        symbol: str = None,
        indent: int = 0,
    ) -> Text:
        """
        Format a debug message with rich styling.

        Args:
            message: The message to format
            level: The debug level
            symbol: Optional symbol to prefix
            indent: Indentation level

        Returns:
            Rich Text object with styling
        """
        # Create indentation
        indent_str = "  " * indent

        # Create styled text
        text = Text()

        # Add prefix with symbol if provided
        if symbol:
            # Style the symbol if we have a style for it
            if symbol in self.symbol_styles:
                text.append(f"{indent_str}{symbol} ", style=self.symbol_styles[symbol])
            else:
                text.append(f"{indent_str}{symbol} ")
        else:
            text.append(indent_str)

        # Add message with level-appropriate styling
        if level in self.level_styles:
            text.append(message, style=self.level_styles[level])
        else:
            text.append(message)

        return text

    def start_thinking_section(self):
        self.console.rule(style="magenta", title="Thinking")

    def end_thinking_section(self):
        self.console.rule(style="magenta", title="Done Thinking")

    def display_debug_message(
        self,
        message: str,
        level: DebugLevel = DebugLevel.STANDARD,
        symbol: str = None,
        indent: int = 0,
    ) -> None:
        """
        Display a formatted debug message to the console.

        Args:
            message: The message to display
            level: The debug level
            symbol: Optional symbol to prefix
            indent: Indentation level
        """
        text = self.format_debug_message(message, level, symbol, indent)
        self.console.print(text)

    def display_debug_panel(
        self, content: str, title: str = "Debug Info", style: str = "cyan"
    ) -> None:
        """
        Display content in a styled debug panel.

        Args:
            content: The content to display
            title: Panel title
            style: Border style
        """
        # Create a ResponsivePanel with centered alignment
        formatted_content = Markdown(content) if "```" in content or "#" in content else content
        panel = ResponsivePanel(
            formatted_content,
            width_percentage=0.9,
            align="left",
            title=title,
            border_style=style,
            padding=(1, 2),
        )
        self.console.print(panel)

    # User and assistant message display
    def display_user_message(self, message: str, user_id: str = "User") -> None:
        """
        Display a user message in a right-aligned panel that takes up 2/3 of screen width.

        Args:
            message: The message content
            user_id: User identifier to show in title
        """
        # Use ResponsivePanel for user messages (right aligned, 2/3 width)
        formatted_content = self.format_content_for_display(message)
        user_panel = ResponsivePanel(
            formatted_content,
            width_percentage=0.67,  # 2/3 of screen width
            align="right",
            title=f"{user_id}",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        self.console.print(user_panel)

    def display_assistant_message(self, message: str, assistant_name: str = "Luna") -> None:
        """
        Display an assistant message in a left-aligned panel that takes up 2/3 of screen width.

        Args:
            message: The message content
            assistant_name: Assistant name to show in title
        """
        # Use ResponsivePanel for assistant messages (left aligned, 2/3 width)
        formatted_content = self.format_content_for_display(message)
        assistant_panel = ResponsivePanel(
            formatted_content,
            width_percentage=0.67,  # 2/3 of screen width
            align="left",
            title=f"{assistant_name}",
            border_style="magenta",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        self.console.print(assistant_panel)

    # Thinking display
    def display_thinking(self, thought_content: str, agent: str) -> None:
        """
        Display an agent's thinking process in a center-aligned panel.

        Args:
            thought_content: The thought process content
            agent: The name of the agent doing the thinking
        """
        # For thinking, we want a centered panel so create a panel and use Align.center
        formatted_content = Markdown(thought_content)
        thinking_panel = ResponsivePanel(
            formatted_content,
            title=f"{agent}'s Inner Thoughts",
            border_style=self.get_agent_style(agent),
            padding=(1, 2),
            width_percentage=0.33,  # 1/3 of screen width
            box=box.ROUNDED,
            align="center",
        )
        centered_panel = Align.center(thinking_panel)
        self.console.print(centered_panel)

    # Tool call display
    def display_tool_call(
        self, source_agent: str, tool_name: str, tool_input: Dict[str, Any], message: str = ""
    ) -> None:
        """
        Display a tool call in a center-aligned panel.

        Args:
            source_agent: The agent making the tool call
            tool_name: Name of the tool being called
            tool_input: Input parameters for the tool
            message: Optional message to display with the tool call
        """
        # Format tool input in a way that ensures it's readable
        if isinstance(tool_input, dict) and len(tool_input) > 0:
            # Use Syntax with word_wrap=True for better readability of long strings
            input_json = json.dumps(tool_input, indent=2, default=str)
            formatted_input = Syntax(input_json, "json", theme="monokai", word_wrap=True)
        else:
            # Fall back to markdown for any non-dict or empty inputs
            input_json = json.dumps(tool_input, indent=2, default=str)
            formatted_input = Markdown(f"```json\n{input_json}\n```")

        # For tool calls, we want a centered panel
        content = Group(
            Markdown(f"**Tool Call:** {message}") if message else Text(""), formatted_input
        )

        tool_panel = ResponsivePanel(
            content,
            title=f"Tool Call: {tool_name}",
            subtitle=f"{source_agent} {self.symbols.DIRECTION_TO} {tool_name}",
            border_style=self.get_agent_style(source_agent),
            padding=(1, 2),
            width_percentage=0.4,  # Slightly wider than before
            align="center",
        )
        centered_panel = Align.center(tool_panel)
        self.console.print(centered_panel)

    def display_tool_response(
        self, target_agent: str, tool_name: str, tool_output: Dict[str, Any]
    ) -> None:
        """
        Display a tool response in a center-aligned panel.

        Args:
            target_agent: The agent receiving the tool response
            tool_name: Name of the tool that was called
            tool_output: Output data from the tool
        """
        # Check for error messages in the tool output
        is_error = False
        if isinstance(tool_output, dict):
            # Various ways errors might be represented
            is_error = (
                tool_output.get("is_error", False)
                or tool_output.get("success", True) is False
                or "error" in tool_output
                or tool_output.get("result") == "Tool execution failed"
            )

        # Format the output based on whether it's an error
        if is_error:
            # For errors, use Markdown with word wrap to ensure full visibility
            error_content = ""

            # Build a properly formatted error message
            if "error" in tool_output:
                error_content += f"**Error:** {tool_output['error']}\n\n"

            if "message" in tool_output:
                error_content += f"**Message:** {tool_output['message']}\n\n"

            if "content" in tool_output:
                error_content += f"**Content:** {tool_output['content']}\n\n"

            if not error_content and "result" in tool_output:
                error_content += f"**Result:** {tool_output['result']}\n\n"

            # If we couldn't extract a good error message, just show the whole thing
            if not error_content:
                error_content = f"```json\n{json.dumps(tool_output, indent=2)}\n```"

            formatted_output = Markdown(error_content)

            # Title and style for error panels
            panel_title = f"Tool Error: {tool_name}"
            panel_style = "red"
        else:
            # For success responses, use standard JSON formatting
            if isinstance(tool_output, dict):
                output_json = json.dumps(tool_output, indent=2, default=str)
                formatted_output = Syntax(output_json, "json", theme="monokai", word_wrap=True)
            elif hasattr(tool_output, "to_dict"):
                output_json = json.dumps(tool_output.to_dict(), indent=2, default=str)
                formatted_output = Syntax(output_json, "json", theme="monokai", word_wrap=True)
            panel_title = f"Tool Response: {tool_name}"
            panel_style = self.get_agent_style(target_agent)

        # For tool responses, we want a centered panel
        content = Group(
            Markdown(f"**Tool {'Error' if is_error else 'Response'}:** {tool_name}"),
            formatted_output,
        )

        tool_panel = ResponsivePanel(
            content,
            title=panel_title,
            subtitle=f"{target_agent} {self.symbols.DIRECTION_FROM} {tool_name}",
            border_style=panel_style,
            padding=(1, 2),
            width_percentage=0.5 if is_error else 0.33,  # Make error panels wider
            align="center",
        )
        centered_panel = Align.center(tool_panel)
        self.console.print(centered_panel)

    # Agent routing display
    def display_agent_request(self, source_agent: str, target_agent: str, message: str) -> None:
        """
        Display an agent request message in a left-aligned panel.

        Args:
            source_agent: The agent sending the request
            target_agent: The agent receiving the request
            message: The message content
        """
        formatted_content = Markdown(f"**{source_agent}:** {message}")
        request_panel = ResponsivePanel(
            formatted_content,
            width_percentage=0.33,  # 1/3 of screen width
            align="left",
            title=f"Agent Routing: {source_agent}",
            subtitle=f"{source_agent} {self.symbols.DIRECTION_TO} {target_agent}",
            border_style=self.get_agent_style(source_agent),
            padding=(1, 2),
        )
        self.console.print(request_panel)

    def display_agent_response(self, source_agent: str, target_agent: str, message: str) -> None:
        """
        Display an agent response message in a right-aligned panel.

        Args:
            source_agent: The agent that sent the original request
            target_agent: The agent sending the response
            message: The message content
        """
        formatted_content = Markdown(f"**{target_agent}:** {message}")
        response_panel = ResponsivePanel(
            formatted_content,
            width_percentage=0.33,  # 1/3 of screen width
            align="right",
            title=f"Agent Routing: {target_agent}",
            subtitle=f"{source_agent} {self.symbols.DIRECTION_FROM} {target_agent}",
            border_style=self.get_agent_style(target_agent),
            padding=(1, 2),
        )
        self.console.print(response_panel)

    # Code display
    def display_code(self, code: str, language: str = "python", title: str = "Code") -> None:
        """
        Display syntax-highlighted code.

        Args:
            code: The code to display
            language: The language for syntax highlighting
            title: Panel title
        """
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        code_panel = ResponsivePanel(
            syntax,
            width_percentage=0.9,
            align="left",
            title=title,
            border_style="green",
            padding=(1, 2),
        )
        self.console.print(code_panel)
