from datetime import datetime, timezone
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.style import Style
from rich.text import Text
from typing import Dict, Optional, Callable, List
import asyncio

console = Console()


class AgentProgress:
    """Manages progress tracking for multiple agents."""

    def __init__(self):
        self.agent_status: Dict[str, Dict[str, str]] = {}
        self.table = Table(show_header=False, box=None, padding=(0, 1))
        self.live = Live(self.table, console=console, refresh_per_second=4)
        self.started = False
        self.update_handlers: List[Callable[[str, Optional[str], str], None]] = []

    def register_handler(self, handler: Callable[[str, Optional[str], str], None]):
        """Register a handler to be called when agent status updates."""
        self.update_handlers.append(handler)
        return handler  # Return handler to support use as decorator

    def unregister_handler(self, handler: Callable[[str, Optional[str], str], None]):
        """Unregister a previously registered handler."""
        if handler in self.update_handlers:
            self.update_handlers.remove(handler)

    def start(self):
        """Start the progress display."""
        if not self.started:
            self.live.start()
            self.started = True

    def stop(self):
        """Stop the progress display."""
        if self.started:
            self.live.stop()
            self.started = False

    def update_status(self, agent_name: str, crypto: Optional[str] = None, status: str = ""):
        """Update the status of an agent."""
        if not self.started:
            return
            
        # 更新状态
        if agent_name not in self.agent_status:
            self.agent_status[agent_name] = {"status": "", "crypto": None}

        if crypto:
            self.agent_status[agent_name]["crypto"] = crypto
        if status:
            self.agent_status[agent_name]["status"] = status
        self.agent_status[agent_name]["timestamp"] = datetime.now(timezone.utc).isoformat()

        # 通知所有注册的处理程序
        for handler in self.update_handlers:
            try:
                handler(agent_name, crypto, status)
            except Exception as e:
                print(f"Error in handler: {e}")

        # 立即刷新显示
        self._refresh_display()

    def get_all_status(self):
        """Get the current status of all agents as a dictionary."""
        return {agent_name: {"crypto": info["crypto"], "status": info["status"], "display_name": self._get_display_name(agent_name)} for agent_name, info in self.agent_status.items()}

    def _get_display_name(self, agent_name: str) -> str:
        """Convert agent_name to a display-friendly format."""
        return agent_name.replace("_agent", "").replace("_", " ").title()

    def _refresh_display(self):
        """Refresh the progress display."""
        self.table.columns.clear()
        self.table.add_column(width=100)

        # Sort agents with Risk Management and Portfolio Management at the bottom
        def sort_key(item):
            agent_name = item[0]
            if "risk_management" in agent_name:
                return (2, agent_name)
            elif "portfolio_management" in agent_name:
                return (3, agent_name)
            else:
                return (1, agent_name)

        for agent_name, info in sorted(self.agent_status.items(), key=sort_key):
            status = info["status"]
            crypto = info["crypto"]
            # Create the status text with appropriate styling
            if status.lower() == "done":
                style = Style(color="green", bold=True)
                symbol = "✓"
            elif status.lower() == "error":
                style = Style(color="red", bold=True)
                symbol = "✗"
            else:
                style = Style(color="yellow")
                symbol = "⋯"

            agent_display = self._get_display_name(agent_name)
            status_text = Text()
            status_text.append(f"{symbol} ", style=style)
            status_text.append(f"{agent_display:<20}", style=Style(bold=True))

            if crypto:
                status_text.append(f"[{crypto}] ", style=Style(color="cyan"))
            status_text.append(status, style=style)

            self.table.add_row(status_text)


# Create a global instance
progress = AgentProgress()
