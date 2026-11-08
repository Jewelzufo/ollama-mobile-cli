"""
CreativeAct Ollama Mobile - Terminal UI Renderer
Provides Rich terminal formatting, Markdown rendering, banners, and status displays.
Includes graceful standard library ANSI fallback when Rich is not available.
"""

import sys
import re

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.status import Status
    from rich import print as rprint
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    class FallbackStatus:
        def __init__(self, message: str, **kwargs):
            self.message = message
        def __enter__(self):
            print(f"⏳ {self.message}")
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    class FallbackConsole:
        def print(self, *args, **kwargs):
            cleaned = []
            for a in args:
                if isinstance(a, str):
                    cleaned.append(re.sub(r"\[/?(bold|dim|cyan|yellow|green|blue|red)\]", "", a))
                else:
                    cleaned.append(str(a))
            print(*cleaned, end=kwargs.get("end", "\n"))

        def input(self, prompt: str = "") -> str:
            clean_prompt = re.sub(r"\[/?(bold|dim|cyan|yellow|green|blue|red)\]", "", prompt)
            return input(clean_prompt)

        def status(self, message: str, **kwargs):
            return FallbackStatus(message, **kwargs)

    console = FallbackConsole()


class TerminalUI:
    @staticmethod
    def print_banner(model: str, url: str):
        if HAS_RICH:
            banner_text = (
                f"[bold cyan]CreativeAct Ollama Mobile[/bold cyan]\n"
                f"[dim]Android Termux TUI Client for Ollama[/dim]\n\n"
                f"[yellow]Server URL:[/yellow] {url}\n"
                f"[green]Active Model:[/green] {model}\n"
                f"[dim]Type /help for slash commands or /exit to quit.[/dim]"
            )
            console.print(Panel(banner_text, border_style="cyan", expand=False))
        else:
            print("==========================================")
            print("       CreativeAct Ollama Mobile")
            print("   Android Termux TUI Client for Ollama")
            print(f"Server URL:   {url}")
            print(f"Active Model: {model}")
            print("Type /help for slash commands or /exit to quit.")
            print("==========================================")

    @staticmethod
    def print_help():
        commands = [
            ("/new", "Start a new conversation (clears history)"),
            ("/exit", "Exit the application gracefully"),
            ("/params", "View and modify Ollama generation parameters"),
            ("/system", "Manage and update system prompts"),
            ("/models", "List and switch available Ollama models"),
            ("/server", "Change Ollama server URL"),
            ("/help", "Display available slash commands")
        ]

        if HAS_RICH:
            table = Table(title="Slash Commands", border_style="cyan")
            table.add_column("Command", style="bold yellow", no_wrap=True)
            table.add_column("Function", style="white")
            for cmd, desc in commands:
                table.add_row(cmd, desc)
            console.print(table)
        else:
            print("\nAvailable Slash Commands:")
            for cmd, desc in commands:
                print(f"  {cmd:<10} - {desc}")
            print()

    @staticmethod
    def print_parameters(params: dict):
        if HAS_RICH:
            table = Table(title="Generation Parameters", border_style="yellow")
            table.add_column("Parameter", style="bold cyan")
            table.add_column("Value", style="green")
            for k, v in params.items():
                table.add_row(k, str(v))
            console.print(table)
            console.print("[dim]Use /params <name> <value> to modify a parameter.[/dim]")
        else:
            print("\nGeneration Parameters:")
            for k, v in params.items():
                print(f"  {k:<16}: {v}")
            print("Use /params <name> <value> to modify a parameter.\n")

    @staticmethod
    def print_markdown(content: str):
        """Render markdown content nicely in terminal."""
        if HAS_RICH:
            md = Markdown(content)
            console.print(Panel(md, border_style="blue", title="Assistant", title_align="left"))
        else:
            print("\n--- Assistant ---")
            print(content)
            print("-----------------\n")

    @staticmethod
    def print_user_message(content: str):
        console.print(f"\n[bold green]You:[/bold green] {content}")

    @staticmethod
    def print_error(message: str):
        console.print(f"[bold red]Error:[/bold red] {message}")

    @staticmethod
    def print_success(message: str):
        console.print(f"[bold green]Success:[/bold green] {message}")

    @staticmethod
    def print_info(message: str):
        console.print(f"[bold cyan]Info:[/bold cyan] {message}")
