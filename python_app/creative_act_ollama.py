#!/usr/bin/env python3
"""
CreativeAct Ollama Mobile - Main REPL Application
Interactive mobile terminal interface for communicating with locally hosted Ollama models.
Optimized for Android Termux with Rich Markdown rendering, live streaming,
and robust loading indicators that cleanly terminate on output.
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

            # Professional loading feedback during initial model load / think phase
            status = console.status(f"[cyan]Thinking... ({model})[/cyan]", spinner="dots")
            status.start()

            stream_started = False
            try:
                stream = client.chat_stream(
                    model=model,
                    messages=messages,
                    options=options,
                    system=system_prompt
                )

                for chunk in stream:
                    if not chunk:
                        continue
                    if not stream_started:
                        # Cleanly terminate loading indicator BEFORE printing any response
                        status.stop()
                        stream_started = True
                        console.print(f"[bold blue]Assistant ({model}) >[/bold blue]\n", end="")

                    # Stream tokens directly to terminal without buffer lag
                    console.print(chunk, end="", highlight=False)
                    sys.stdout.flush()
                    full_response += chunk

                if not stream_started:
                    status.stop()

                console.print("\n")

            except Exception as e:
                # Stop status first so error message is never wiped by transient cleanup
                if not stream_started:
                    try:
                        status.stop()
                    except Exception:
                        pass
                console.print()
                TerminalUI.print_error(f"Generation error: {e}")
                continue
            finally:
                if not stream_started:
                    try:
                        status.stop()
                    except Exception:
                        pass

            if full_response:
                conversation.add_message("assistant", full_response)

                # Rich Markdown Rendering:
                # If the response contains markdown formatting (code blocks, tables, headers, lists, bold),
                # provide a high-contrast styled Markdown block for mobile readability
                has_markdown = any(m in full_response for m in ["```", "### ", "## ", "# ", "|---", "- [ ]", " - ", " * ", "**"])
                if has_markdown:
                    TerminalUI.print_markdown(full_response, title=f"Assistant ({model})")
            elif not stream_started:
                TerminalUI.print_error(f"No response received from model '{model}'. Verify that the model is loaded in Ollama.")

        except (KeyboardInterrupt, EOFError):
            console.print("\n")
            TerminalUI.print_info("Exiting CreativeAct Ollama Mobile. Goodbye!")
            break
        except Exception as e:
            TerminalUI.print_error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
