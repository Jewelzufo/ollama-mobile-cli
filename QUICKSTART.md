# CreativeAct Ollama Mobile - Termux Quickstart Guide

Get **CreativeAct Ollama Mobile** running on your Android device via Termux in under 5 minutes.

---

## Step 1: Install Termux
1. Download and install **Termux** from [F-Droid](https://f-droid.org/packages/com.termux/) (recommended) rather than the Google Play Store (which is deprecated).
2. Open Termux and update package lists:
   ```bash
   pkg update && pkg upgrade -y
   ```

---

## Step 2: Install Python & Git
Install Python 3, Git, and build essentials required for the Python environment:
```bash
pkg install -y python git clang make libffi openssl
```

---

## Step 3: Get Project Files & Install Dependencies
1. Clone or copy your project files into Termux (e.g. into `~/creative_act_ollama/`).
2. Navigate to the project directory and install the required Python packages (`rich`, `requests`, `prompt_toolkit`):
   ```bash
   cd creative_act_ollama
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   *(Alternatively, run the provided automated setup script: `bash termux_setup.sh`)*

---

## Step 4: Start Ollama (Local AI Server)
Ollama runs locally on your device or a networked server. In a **second/separate Termux session** (swipe from the left edge of your screen and open a new session):
```bash
ollama serve
```
*Note: Make sure you have pulled your desired model beforehand, e.g., `ollama pull llama3`.*

---

## Step 5: Run CreativeAct Ollama Mobile
Return to your main Termux session and launch the REPL application:
```bash
python creative_act_ollama.py
```

---

## Slash Command Cheat Sheet
Once inside the REPL, use these slash commands anytime:
- `/new` - Start a new conversation (clears history)
- `/params` - View or modify generation parameters (`temperature`, `top_p`, etc.)
- `/system` - View or update the system prompt
- `/models` - List and switch available Ollama models
- `/server` - Change the Ollama server URL
- `/help` - Display all available commands
- `/exit` - Exit the application gracefully
