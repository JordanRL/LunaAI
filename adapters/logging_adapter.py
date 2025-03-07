"""
Logging adapter for Luna system using Python's logging module.

This adapter creates a flexible logging system that supports both:
- Console output using Rich
- File output for persistent logs
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Dict, List, Optional, Union

from rich.console import Console
from rich.logging import RichHandler

from adapters.console_adapter import DebugLevel, DebugSymbols


class LoggingAdapter:
    """
    Logging adapter for Luna that supports both console and file logging.
    Integrates with Luna's debug levels and formatting conventions.
    """

    def __init__(
        self,
        logger_name: str = "luna",
        console: Optional[Console] = None,
        log_file: Optional[str] = None,
        level: Union[int, DebugLevel] = DebugLevel.STANDARD,
    ):
        """
        Initialize the logging adapter.

        Args:
            logger_name: Name for the logger
            console: Optional Rich console instance for output
            log_file: Optional file path for log output
            level: Initial logging level (can be DebugLevel enum or logging module level)
        """
        self.logger_name = logger_name
        self.symbols = DebugSymbols()
        self.console = console or Console()

        # Create logger
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(self._translate_level(level))
        self.logger.propagate = False

        # Clear any existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()

        # Configure console logging with Rich
        rich_handler = RichHandler(
            console=self.console, rich_tracebacks=True, markup=True, show_time=True, show_path=False
        )
        rich_handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(rich_handler)

        # Configure file logging if specified
        if log_file:
            self._setup_file_logging(log_file)

        # Mapping between DebugLevel and logging levels
        self.level_mapping = {
            DebugLevel.NONE: logging.CRITICAL,
            DebugLevel.MINIMAL: logging.WARNING,
            DebugLevel.STANDARD: logging.INFO,
            DebugLevel.VERBOSE: logging.DEBUG,
            DebugLevel.TRACE: logging.DEBUG - 5,  # Custom deeper level
        }

        # Agent styles for visualization (matching console_adapter)
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

    def _translate_level(self, level: Union[int, DebugLevel]) -> int:
        """
        Translate between DebugLevel and logging module levels.

        Args:
            level: Level to translate

        Returns:
            Corresponding logging module level
        """
        if isinstance(level, DebugLevel):
            return self.level_mapping.get(level, logging.INFO)
        return level

    def _setup_file_logging(self, log_file: str) -> None:
        """
        Set up file logging with rotation.

        Args:
            log_file: Path to log file
        """
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Create a rotating file handler (10 MB max size, keep 5 backups)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )

        # Plain text formatter for file logs
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def set_level(self, level: Union[int, DebugLevel]) -> None:
        """
        Set the logging level.

        Args:
            level: New logging level (can be DebugLevel enum or logging module level)
        """
        translated_level = self._translate_level(level)
        self.logger.setLevel(translated_level)

        # Update all handlers to match this level
        for handler in self.logger.handlers:
            handler.setLevel(translated_level)

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

    def format_agent_message(self, agent_name: str, message: str) -> str:
        """
        Format a message with agent name.

        Args:
            agent_name: The name of the agent
            message: The message text

        Returns:
            Formatted message string with agent info
        """
        return f"[{self.get_agent_style(agent_name)}]{agent_name}[/]: {message}"

    def add_file_handler(
        self, log_file: str, level: Optional[Union[int, DebugLevel]] = None
    ) -> None:
        """
        Add a new file handler to the logger.

        Args:
            log_file: Path to log file
            level: Optional logging level for this handler
        """
        if level is None:
            level = self.logger.level
        else:
            level = self._translate_level(level)

        self._setup_file_logging(log_file)

    def remove_file_handlers(self) -> None:
        """Remove all file handlers from the logger."""
        for handler in list(self.logger.handlers):
            if isinstance(handler, RotatingFileHandler):
                self.logger.removeHandler(handler)

    def debug(
        self, message: str, symbol: Optional[str] = None, agent: Optional[str] = None
    ) -> None:
        """
        Log a debug message.

        Args:
            message: The message to log
            symbol: Optional symbol to prefix
            agent: Optional agent name for context
        """
        formatted = self._format_message(message, symbol, agent)
        self.logger.debug(formatted)

    def info(self, message: str, symbol: Optional[str] = None, agent: Optional[str] = None) -> None:
        """
        Log an info message.

        Args:
            message: The message to log
            symbol: Optional symbol to prefix
            agent: Optional agent name for context
        """
        formatted = self._format_message(message, symbol, agent)
        self.logger.info(formatted)

    def warning(
        self, message: str, symbol: Optional[str] = None, agent: Optional[str] = None
    ) -> None:
        """
        Log a warning message.

        Args:
            message: The message to log
            symbol: Optional symbol to prefix
            agent: Optional agent name for context
        """
        symbol = symbol or self.symbols.WARNING
        formatted = self._format_message(message, symbol, agent)
        self.logger.warning(formatted)

    def error(
        self, message: str, symbol: Optional[str] = None, agent: Optional[str] = None
    ) -> None:
        """
        Log an error message.

        Args:
            message: The message to log
            symbol: Optional symbol to prefix
            agent: Optional agent name for context
        """
        symbol = symbol or self.symbols.ERROR
        formatted = self._format_message(message, symbol, agent)
        self.logger.error(formatted)

    def critical(
        self, message: str, symbol: Optional[str] = None, agent: Optional[str] = None
    ) -> None:
        """
        Log a critical message.

        Args:
            message: The message to log
            symbol: Optional symbol to prefix
            agent: Optional agent name for context
        """
        symbol = symbol or self.symbols.ERROR
        formatted = self._format_message(message, symbol, agent)
        self.logger.critical(formatted)

    def _format_message(
        self, message: str, symbol: Optional[str] = None, agent: Optional[str] = None
    ) -> str:
        """
        Format a log message with optional symbol and agent name.

        Args:
            message: The message to format
            symbol: Optional symbol to prefix
            agent: Optional agent name for context

        Returns:
            Formatted message string
        """
        parts = []

        # Add symbol if provided
        if symbol:
            parts.append(f"{symbol} ")

        # Add agent name if provided
        if agent:
            # When logging to file, the Rich markup will be stripped
            parts.append(f"[{self.get_agent_style(agent)}]{agent}[/]: ")

        # Add the message
        parts.append(message)

        return "".join(parts)

    def log_tool_call(self, source_agent: str, tool_name: str, tool_input: Dict) -> None:
        """
        Log a tool call.

        Args:
            source_agent: The agent making the tool call
            tool_name: Name of the tool being called
            tool_input: Input parameters for the tool
        """
        message = f"Tool call: {tool_name}"
        self.info(message, symbol=self.symbols.TOOL, agent=source_agent)

        # Log tool input parameters at debug level
        params_str = ", ".join(f"{k}={v}" for k, v in tool_input.items())
        self.debug(f"Tool params: {params_str}", agent=source_agent)

    def log_tool_response(self, target_agent: str, tool_name: str, success: bool) -> None:
        """
        Log a tool response.

        Args:
            target_agent: The agent receiving the tool response
            tool_name: Name of the tool that was called
            success: Whether the tool call was successful
        """
        symbol = self.symbols.SUCCESS if success else self.symbols.ERROR
        status = "succeeded" if success else "failed"
        message = f"Tool response: {tool_name} {status}"
        self.info(message, symbol=symbol, agent=target_agent)

    def log_agent_routing(self, source_agent: str, target_agent: str, direction: str = "→") -> None:
        """
        Log agent routing.

        Args:
            source_agent: The sending agent
            target_agent: The receiving agent
            direction: Direction symbol
        """
        message = f"Routing: {source_agent} {direction} {target_agent}"
        self.info(message, symbol=self.symbols.ROUTING)

    def log_memory_operation(self, operation: str, agent: Optional[str] = None) -> None:
        """
        Log a memory operation.

        Args:
            operation: The memory operation description
            agent: Optional agent performing the operation
        """
        message = f"Memory: {operation}"
        self.info(message, symbol=self.symbols.MEMORY, agent=agent)

    def log_thinking(self, thought: str, agent: str) -> None:
        """
        Log an agent's thinking process.

        Args:
            thought: The thought content
            agent: The agent doing the thinking
        """
        message = f"Thinking: {thought}"
        self.debug(message, symbol=self.symbols.THINKING, agent=agent)
