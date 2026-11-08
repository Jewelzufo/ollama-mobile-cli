#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# CreativeAct Ollama Mobile - Termux Installation Script
# Automatically sets up Python, dependencies, and Ollama bridge in Android Termux.
# ==============================================================================

echo "=== Updating Termux Packages ==="
pkg update -y && pkg upgrade -y

echo "=== Installing Python, Git, and Build Dependencies ==="
pkg install -y python git clang make libffi openssl

echo "=== Upgrading pip ==="
pip install --upgrade pip

echo "=== Installing Python Requirements (Rich, Requests, Prompt Toolkit) ==="
pip install -r requirements.txt

echo "=== Setup Complete! ==="
echo "To start Ollama (in a separate Termux session):"
echo "  ollama serve"
echo ""
echo "To run CreativeAct Ollama Mobile:"
echo "  python creative_act_ollama.py"
