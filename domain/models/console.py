from typing import Callable

from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderableType, RenderResult
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.status import Status
from rich.style import StyleType


class ResponsivePanel:
    """A panel that adapts its content size based on container dimensions."""

    def __init__(
        self,
        renderable: RenderableType,
        width_percentage: float = 0.7,
        align: str = "left",
        **panel_kwargs,
    ):
        """
        Initialize a responsive panel.

        Args:
          renderable: The content to display
          width_percentage: Width as percentage of container (0.0-1.0)
          align: Alignment ("left" or "right")
          **panel_kwargs: Additional kwargs for Panel constructor
        """
        self.renderable = renderable
        self.width_percentage = width_percentage
        self.align = align
        self.panel_kwargs = panel_kwargs

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        # Calculate width based on container width
        available_width = options.max_width
        panel_width = int(available_width * self.width_percentage)

        # Create panel with calculated width
        panel = Panel(self.renderable, width=panel_width, **self.panel_kwargs)

        # Apply alignment
        if self.align == "right":
            aligned_panel = Align.right(panel)
        elif self.align == "center":
            aligned_panel = Align.center(panel)
        else:
            aligned_panel = Align.left(panel)

        # Yield the panel for rendering
        yield aligned_panel
