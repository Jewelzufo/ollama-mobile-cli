#!/usr/bin/env python3
"""
CreativeAct Ollama Mobile - Main REPL Application
Interactive mobile terminal interface for communicating with locally hosted Ollama models.
Optimized for Android Termux.
"""

import sys
import os

from config import ConfigManager
from conversation import ConversationManager
from ollama_client import OllamaClient
from ui import TerminalUI, console
from commands import CommandDispatcher

def main():
    config = ConfigManager()
    conversation = ConversationManager()
    client = OllamaClient(base_url=config.get("ollama_url"))
    dispatcher = CommandDispatcher(config, conversation, client)

    TerminalUI.print_banner(config.get("model"), config.get("ollama_url"))

    # Quick connection check on startup
    if not client.check_connection():
        TerminalUI.print_error(f"Could not connect to Ollama server at {config.get('ollama_url')}.")
        TerminalUI.print_info("Make sure Ollama is running (e.g. 'ollama serve') and accessible.")
    else:
        TerminalUI.print_success("Connected to Ollama server successfully!")

    while True:
        try:
            # Prompt user
            user_input = console.input("\n[bold green]You > [/bold green]").strip()
            if not user_input:
                continue

            # Check for slash command
            if user_input.startswith("/"):
                should_exit = dispatcher.handle_command(user_input)
                if should_exit:
                    break
                continue

            # Regular chat flow
            conversation.add_message("user", user_input)
            
            model = config.get("model")
            options = config.get("parameters")
            system_prompt = config.get("system_prompt")
            messages = conversation.get_api_messages()

            console.print()
            full_response = ""
            
            with console.status("[cyan]Thinking...", spinner="dots"):
                try:
                    stream = client.chat_stream(
                        model=model,
                        messages=messages,
                        options=options,
                        system=system_prompt
                    )
                    
                    # Stream chunks
                    first_chunk = True
                    for chunk in stream:
                        if first_chunk:
                            # Clear status and print header for assistant
                            console.print("[bold blue]Assistant > [/bold blue]", end="")
                            first_chunk = False
                        console.print(chunk, end="")
                        full_response += chunk
                    console.print("\n")
                except Exception as e:
                    TerminalUI.print_error(str(e))
                    continue

            if full_response:
                conversation.add_message("assistant", full_response)

        except (KeyboardInterrupt, EOFError):
            console.print("\n")
            TerminalUI.print_info("Exiting CreativeAct Ollama Mobile. Goodbye!")
            break
        except Exception as e:
            TerminalUI.print_error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
