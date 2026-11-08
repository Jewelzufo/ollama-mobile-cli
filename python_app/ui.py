"""
CreativeAct Ollama Mobile - Terminal UI Renderer
Provides Rich terminal formatting, Markdown rendering, banners, and status displays.
"""

import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.status import Status
from rich import print as rprint

console = Console()

class TerminalUI:
    @staticmethod
    def print_banner(model: str, url: str):
        banner_text = (
            f"[bold cyan]CreativeAct Ollama Mobile[/bold cyan]\n"
            f"[dim]Android Termux TUI Client for Ollama[/dim]\n\n"
            f"[yellow]Server URL:[/yellow] {url}\n"
            f"[green]Active Model:[/green] {model}\n"
            f"[dim]Type /help for slash commands or /exit to quit.[/dim]"
        )
        console.print(Panel(banner_text, border_style="cyan", expand=False))

    @staticmethod
    def print_help():
        table = Table(title="Slash Commands", border_style="cyan")
        table.add_column("Command", style="bold yellow", no_wrap=True)
        table.add_column("Function", style="white")

        commands = [
            ("/new", "Start a new conversation (clears history)"),
            ("/exit", "Exit the application gracefully"),
            ("/params", "View and modify Ollama generation parameters"),
            ("/system", "Manage and update system prompts"),
            ("/models", "List and switch available Ollama models"),
            ("/server", "Change Ollama server URL"),
            ("/help", "Display available slash commands")
        ]

        for cmd, desc in commands:
            table.add_row(cmd, desc)

        console.print(table)

    @staticmethod
    def print_parameters(params: dict):
        table = Table(title="Generation Parameters", border_style="yellow")
        table.add_column("Parameter", style="bold cyan")
        table.add_column("Value", style="green")

        for k, v in params.items():
            table.add_row(k, str(v))

        console.print(table)
        console.print("[dim]Use /params <name> <value> to modify a parameter.[/dim]")

    @staticmethod
    def print_markdown(content: str):
        """Render markdown content nicely in terminal."""
        md = Markdown(content)
        console.print(Panel(md, border_style="blue", title="Assistant", title_align="left"))

    @staticmethod
    def print_user_message(content: str):
        console.print(f"\n[bold green]You:[/bold green] {content}")

    @staticmethod
    def print_error(message: str):
        console.print(f"[bold red]Error:[/bold red] {message}", style="red")

    @staticmethod
    def print_success(message: str):
        console.print(f"[bold green]Success:[/bold green] {message}")

    @staticmethod
    def print_info(message: str):
        console.print(f"[bold cyan]Info:[/bold cyan] {message}")
