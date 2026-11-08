# CreativeAct Ollama Mobile

**CreativeAct Ollama Mobile** is a production-quality Python REPL application designed specifically for Android devices running **Termux**. It provides a polished, feature-rich terminal user interface (TUI) powered by **Rich** for communicating with locally hosted **Ollama** LLM models.

---

## Features

- **Interactive Mobile Terminal REPL**: Optimized for narrow mobile screens, touch keyboards, and Termux terminal constraints.
- **Rich Markdown Rendering**: Headings, inline code, fenced code blocks with syntax highlighting, lists, blockquotes, and tables.
- **Interactive Slash Commands**:
  - `/new` - Start a new conversation (clears history)
  - `/exit` - Exit the application gracefully
  - `/params` - View and modify generation parameters (`temperature`, `top_p`, `top_k`, `num_ctx`, `repeat_penalty`, `seed`)
  - `/system` - View and update system prompts
  - `/models` - List and switch available Ollama models
  - `/server` - Change Ollama server URL
  - `/help` - Display available commands
- **Streaming Responses**: Real-time token streaming with animated loading indicators and elapsed time counters.
- **Persistent Configuration & History**: Automatically saves settings and chat history in `~/.config/creative_act_ollama/`.

---

## Termux Installation Guide

1. **Install Termux** from F-Droid (recommended) or Google Play Store.
2. **Open Termux** and run the setup script or install manually:
   ```bash
   pkg update && pkg install -y python git
   pip install -r requirements.txt
   ```
3. **Start Ollama** (in a separate Termux session or Termux:API / PRoot container depending on device architecture):
   ```bash
   ollama serve
   ```
4. **Run the Application**:
   ```bash
   python creative_act_ollama.py
   ```

---

## Running Unit Tests

To run the comprehensive unit test suite:
```bash
python -m unittest test_creative_act.py
```
