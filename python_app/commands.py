"""
CreativeAct Ollama Mobile - Command Dispatcher
Handles parsing and execution of slash commands.
"""

from typing import List, Any
from ui import TerminalUI, console
from config import ConfigManager
from conversation import ConversationManager
from ollama_client import OllamaClient

class CommandDispatcher:
    def __init__(self, config: ConfigManager, conversation: ConversationManager, client: OllamaClient):
        self.config = config
        self.conversation = conversation
        self.client = client

    def handle_command(self, user_input: str) -> bool:
        """
        Handles slash commands.
        Returns True if the application should exit, False otherwise.
        """
        parts = user_input.strip().split()
        if not parts:
            return False

        cmd = parts[0].lower()
        args = parts[1:]

        if cmd == "/exit":
            TerminalUI.print_info("Exiting CreativeAct Ollama Mobile. Goodbye!")
            return True

        elif cmd == "/new":
            self.conversation.clear()
            TerminalUI.print_success("Started a new conversation history.")

        elif cmd == "/help":
            TerminalUI.print_help()

        elif cmd == "/params":
            if not args:
                TerminalUI.print_parameters(self.config.get("parameters", {}))
            elif len(args) == 2:
                param_name = args[0]
                raw_val = args[1]
                # Try parsing value (int, float, or string)
                val: Any = raw_val
                try:
                    if "." in raw_val:
                        val = float(raw_val)
                    else:
                        val = int(raw_val)
                except ValueError:
                    if raw_val.lower() == "true":
                        val = True
                    elif raw_val.lower() == "false":
                        val = False

                if self.config.update_parameter(param_name, val):
                    TerminalUI.print_success(f"Updated parameter '{param_name}' to {val}")
                else:
                    TerminalUI.print_error(f"Unknown parameter '{param_name}'")
            else:
                TerminalUI.print_error("Usage: /params [name] [value]")

        elif cmd == "/system":
            if not args:
                current_sys = self.config.get("system_prompt", "")
                TerminalUI.print_info(f"Current System Prompt:\n{current_sys}")
            else:
                new_sys = " ".join(args)
                self.config.set("system_prompt", new_sys)
                TerminalUI.print_success("System prompt updated successfully.")

        elif cmd == "/server":
            if not args:
                TerminalUI.print_info(f"Current Ollama URL: {self.config.get('ollama_url')}")
            else:
                new_url = args[0]
                self.config.set("ollama_url", new_url)
                self.client.base_url = new_url.rstrip("/")
                TerminalUI.print_success(f"Ollama server URL updated to: {new_url}")

        elif cmd == "/models":
            try:
                with console.status("[cyan]Fetching available models..."):
                    models = self.client.list_models()
                if not models:
                    TerminalUI.print_error("No models found on Ollama server.")
                else:
                    current_model = self.config.get("model")
                    console.print("\n[bold yellow]Available Models:[/bold yellow]")
                    for m in models:
                        prefix = " > " if m == current_model else "   "
                        console.print(f"{prefix}[cyan]{m}[/cyan]")
                    
                    if args:
                        selected = args[0]
                        if selected in models:
                            self.config.set("model", selected)
                            TerminalUI.print_success(f"Switched active model to: {selected}")
                        else:
                            TerminalUI.print_error(f"Model '{selected}' not found in available models.")
                    else:
                        console.print("[dim]Use /models <model_name> to switch active model.[/dim]")
            except Exception as e:
                TerminalUI.print_error(str(e))

        else:
            TerminalUI.print_error(f"Unknown command '{cmd}'. Type /help for available commands.")

        return False
