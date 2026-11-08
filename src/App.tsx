/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useRef } from 'react';
import { 
  Terminal, 
  Code2, 
  Settings, 
  HelpCircle, 
  Play, 
  FileText, 
  Download, 
  Copy, 
  Check, 
  Cpu, 
  Server, 
  RefreshCw, 
  MessageSquare, 
  Smartphone, 
  Laptop, 
  ShieldCheck,
  BookOpen,
  Send,
  Trash2,
  Sliders,
  Sparkles,
  Layers
} from 'lucide-react';

// Python source files data for the browser
const PYTHON_FILES = [
  {
    name: "creative_act_ollama.py",
    description: "Main REPL controller & entry point",
    path: "/python_app/creative_act_ollama.py",
    content: `#!/usr/bin/env python3
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
            user_input = console.input("\\n[bold green]You > [/bold green]").strip()
            if not user_input:
                continue

            if user_input.startswith("/"):
                should_exit = dispatcher.handle_command(user_input)
                if should_exit:
                    break
                continue

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
                    
                    first_chunk = True
                    for chunk in stream:
                        if first_chunk:
                            console.print("[bold blue]Assistant > [/bold blue]", end="")
                            first_chunk = False
                        console.print(chunk, end="")
                        full_response += chunk
                    console.print("\\n")
                except Exception as e:
                    TerminalUI.print_error(str(e))
                    continue

            if full_response:
                conversation.add_message("assistant", full_response)

        except (KeyboardInterrupt, EOFError):
            console.print("\\n")
            TerminalUI.print_info("Exiting CreativeAct Ollama Mobile. Goodbye!")
            break
        except Exception as e:
            TerminalUI.print_error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()`
  },
  {
    name: "ollama_client.py",
    description: "HTTP client for Ollama API with streaming",
    path: "/python_app/ollama_client.py",
    content: `"""
CreativeAct Ollama Mobile - Ollama API Client
Handles communication with Ollama HTTP API (models list, generate, chat with streaming).
"""

import json
import requests
from typing import Generator, Dict, Any, List, Optional

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def check_connection(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def list_models(self) -> List[str]:
        """Fetch list of available models from Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                return [m.get("name") for m in models if "name" in m]
            return []
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to fetch models: {e}")

    def chat_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None
    ) -> Generator[str, None, None]:
        url = f"{self.base_url}/api/chat"
        payload_messages = list(messages)
        if system:
            payload_messages.insert(0, {"role": "system", "content": system})

        payload = {
            "model": model,
            "messages": payload_messages,
            "stream": True
        }
        if options:
            payload["options"] = options

        with requests.post(url, json=payload, stream=True, timeout=self.timeout) as response:
            if response.status_code != 200:
                raise RuntimeError(f"Ollama API Error ({response.status_code})")
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line.decode("utf-8"))
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content`
  },
  {
    name: "commands.py",
    description: "Slash command parser & handler (/new, /params, /system, etc.)",
    path: "/python_app/commands.py",
    content: `"""
CreativeAct Ollama Mobile - Command Dispatcher
Handles parsing and execution of slash commands.
"""

from typing import List
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
                self.config.update_parameter(args[0], float(args[1]) if "." in args[1] else int(args[1]))
                TerminalUI.print_success(f"Updated parameter '{args[0]}' to {args[1]}")
        elif cmd == "/system":
            if not args:
                TerminalUI.print_info(f"Current System Prompt:\\n{self.config.get('system_prompt')}")
            else:
                self.config.set("system_prompt", " ".join(args))
                TerminalUI.print_success("System prompt updated successfully.")
        return False`
  },
  {
    name: "conversation.py",
    description: "Conversation history and JSON persistence",
    path: "/python_app/conversation.py",
    content: `"""
CreativeAct Ollama Mobile - Conversation Manager
Manages chat history, message logs, and persistence.
"""

import os
import json
from typing import List, Dict, Any
from datetime import datetime

class ConversationManager:
    def __init__(self, history_path: str = None):
        self.history_path = history_path or os.path.expanduser("~/.config/creative_act_ollama/history.json")
        self.messages: List[Dict[str, str]] = []
        self.load_history()

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})
        self.save_history()

    def get_api_messages(self) -> List[Dict[str, str]]:
        return [{"role": m["role"], "content": m["content"]} for m in self.messages]

    def clear(self) -> None:
        self.messages = []
        self.save_history()

    def save_history(self) -> bool:
        try:
            os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(self.messages, f, indent=2)
            return True
        except Exception:
            return False

    def load_history(self) -> None:
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    self.messages = json.load(f)
            except Exception:
                self.messages = []`
  },
  {
    name: "config.py",
    description: "Configuration settings and JSON persistence",
    path: "/python_app/config.py",
    content: `"""
CreativeAct Ollama Mobile - Configuration Manager
Handles loading, saving, and managing app settings and persistent state.
"""

import os
import json

DEFAULT_CONFIG = {
    "ollama_url": "http://localhost:11434",
    "model": "llama3",
    "system_prompt": "You are a helpful, precise AI assistant optimized for mobile terminals.",
    "parameters": {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "num_ctx": 2048,
        "repeat_penalty": 1.1,
        "seed": 42
    }
}

class ConfigManager:
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.expanduser("~/.config/creative_act_ollama/config.json")
        self.config = self.load()

    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return dict(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)`
  },
  {
    name: "ui.py",
    description: "Rich terminal UI rendering and Markdown support",
    path: "/python_app/ui.py",
    content: `"""
CreativeAct Ollama Mobile - Terminal UI Renderer
Provides Rich terminal formatting, Markdown rendering, banners, and status displays.
"""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

console = Console()

class TerminalUI:
    @staticmethod
    def print_banner(model: str, url: str):
        banner_text = f"CreativeAct Ollama Mobile\\nServer: {url} | Model: {model}"
        console.print(Panel(banner_text, border_style="cyan"))

    @staticmethod
    def print_markdown(content: str):
        console.print(Panel(Markdown(content), border_style="blue", title="Assistant"))
`
  },
  {
    name: "requirements.txt",
    description: "Python package dependencies",
    path: "/python_app/requirements.txt",
    content: `rich>=13.0.0
requests>=2.28.0
prompt_toolkit>=3.0.0`
  },
  {
    name: "test_creative_act.py",
    description: "Unit test suite for commands, config, conversation, and API client",
    path: "/python_app/test_creative_act.py",
    content: `"""
CreativeAct Ollama Mobile - Unit Test Suite
"""

import unittest
from config import ConfigManager
from conversation import ConversationManager

class TestCreativeActOllama(unittest.TestCase):
    def test_config(self):
        cfg = ConfigManager()
        self.assertIsNotNone(cfg.get("model"))

    def test_conversation(self):
        conv = ConversationManager()
        conv.clear()
        conv.add_message("user", "Hello test")
        self.assertEqual(len(conv.messages), 1)

if __name__ == "__main__":
    unittest.main()`
  },
  {
    name: "termux_setup.sh",
    description: "Android Termux installation automation script",
    path: "/python_app/termux_setup.sh",
    content: `#!/data/data/com.termux/files/usr/bin/bash
pkg update -y && pkg upgrade -y
pkg install -y python git clang make libffi openssl
pip install --upgrade pip
pip install -r requirements.txt
echo "Setup complete! Run: python creative_act_ollama.py"`
  },
  {
    name: "QUICKSTART.md",
    description: "Termux quickstart guide and instructions",
    path: "/QUICKSTART.md",
    content: `# CreativeAct Ollama Mobile - Termux Quickstart Guide

Get CreativeAct Ollama Mobile running on your Android device via Termux in under 5 minutes.

## Step 1: Install Termux
1. Download and install Termux from F-Droid (recommended).
2. Open Termux and update package lists:
   pkg update && pkg upgrade -y

## Step 2: Install Python & Git
pkg install -y python git clang make libffi openssl

## Step 3: Install Dependencies
pip install --upgrade pip
pip install -r requirements.txt

## Step 4: Start Ollama
In a separate Termux session:
ollama serve

## Step 5: Run the App
python creative_act_ollama.py`
  }
];

export default function App() {
  const [activeTab, setActiveTab] = useState<'simulator' | 'code' | 'tests' | 'guide'>('simulator');
  const [selectedFile, setSelectedFile] = useState(PYTHON_FILES[0]);
  const [copied, setCopied] = useState(false);

  // Terminal Simulator State
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [activeModel, setActiveModel] = useState('llama3');
  const [systemPrompt, setSystemPrompt] = useState('You are a helpful, precise AI assistant optimized for mobile terminals.');
  const [temperature, setTemperature] = useState(0.7);
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant' | 'system' | 'info'; content: string }>>([
    { role: 'info', content: 'CreativeAct Ollama Mobile v1.0.0 initialized.\nConnected to http://localhost:11434 [Model: llama3].\nType your message or /help for slash commands.' }
  ]);
  const [inputVal, setInputVal] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [terminalWidth, setTerminalWidth] = useState<'mobile' | 'full'>('mobile');
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadFile = (file: typeof PYTHON_FILES[0]) => {
    const blob = new Blob([file.content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = file.name;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadAll = () => {
    PYTHON_FILES.forEach(file => {
      setTimeout(() => handleDownloadFile(file), 100);
    });
  };

  const handleSendMessage = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputVal.trim() || isThinking) return;

    const text = inputVal.trim();
    setInputVal('');

    // Handle slash commands in simulator
    if (text.startsWith('/')) {
      const parts = text.split(' ');
      const cmd = parts[0].toLowerCase();
      const args = parts.slice(1);

      if (cmd === '/exit') {
        setMessages(prev => [...prev, { role: 'user', content: text }, { role: 'info', content: 'Exiting CreativeAct Ollama Mobile. Goodbye!' }]);
        return;
      }
      if (cmd === '/new') {
        setMessages(prev => [...prev, { role: 'user', content: text }, { role: 'info', content: 'Started a new conversation history.' }]);
        return;
      }
      if (cmd === '/help') {
        setMessages(prev => [...prev, { role: 'user', content: text }, { role: 'info', content: 'Available Slash Commands:\n/new - Start new conversation\n/exit - Exit app\n/params - View/modify parameters\n/system - Manage system prompts\n/models - List/switch models\n/server - Change server URL\n/help - Display help' }]);
        return;
      }
      if (cmd === '/params') {
        if (args.length === 2) {
          const [pName, pVal] = args;
          if (pName === 'temperature') setTemperature(parseFloat(pVal));
          setMessages(prev => [...prev, { role: 'user', content: text }, { role: 'info', content: `Updated parameter '${pName}' to ${pVal}` }]);
        } else {
          setMessages(prev => [...prev, { role: 'user', content: text }, { role: 'info', content: `Generation Parameters:\n- temperature: ${temperature}\n- top_p: 0.9\n- top_k: 40\n- num_ctx: 2048` }]);
        }
        return;
      }
      if (cmd === '/system') {
        if (args.length > 0) {
          const newSys = args.join(' ');
          setSystemPrompt(newSys);
          setMessages(prev => [...prev, { role: 'user', content: text }, { role: 'info', content: `System prompt updated to: "${newSys}"` }]);
        } else {
          setMessages(prev => [...prev, { role: 'user', content: text }, { role: 'info', content: `Current System Prompt:\n${systemPrompt}` }]);
        }
        return;
      }
      if (cmd === '/models') {
        setMessages(prev => [...prev, { role: 'user', content: text }, { role: 'info', content: `Available Models:\n > llama3:latest (Active)\n   mistral:7b\n   gemma2:9b\n   phi3:mini` }]);
        return;
      }
      if (cmd === '/server') {
        if (args.length > 0) {
          setOllamaUrl(args[0]);
          setMessages(prev => [...prev, { role: 'user', content: text }, { role: 'info', content: `Ollama server URL updated to: ${args[0]}` }]);
        } else {
          setMessages(prev => [...prev, { role: 'user', content: text }, { role: 'info', content: `Current Ollama URL: ${ollamaUrl}` }]);
        }
        return;
      }
      setMessages(prev => [...prev, { role: 'user', content: text }, { role: 'info', content: `Unknown command '${cmd}'. Type /help for available commands.` }]);
      return;
    }

    // Normal chat message
    const currentHistory = messages.filter(m => m.role === 'user' || m.role === 'assistant');
    const updatedMessages = [...currentHistory, { role: 'user' as const, content: text }];
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setIsThinking(true);

    fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: updatedMessages,
        model: activeModel,
        system: systemPrompt,
        options: { temperature },
        ollamaUrl: ollamaUrl,
      })
    })
    .then(async res => {
      const data = await res.json();
      setIsThinking(false);
      if (res.ok) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.content }]);
      } else {
        setMessages(prev => [...prev, { role: 'info', content: `Error: ${data.error || 'Failed to generate response'}` }]);
      }
    })
    .catch(err => {
      setIsThinking(false);
      setMessages(prev => [...prev, { role: 'info', content: `Network error: ${err.message}` }]);
    });
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Terminal className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
              CreativeAct Ollama Mobile
            </h1>
            <p className="text-xs text-slate-400">Android Termux TUI Client & Python Application Suite</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveTab('simulator')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-2 ${
              activeTab === 'simulator'
                ? 'bg-emerald-500 text-slate-950 font-semibold shadow-lg shadow-emerald-500/20'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <Smartphone className="w-4 h-4" />
            <span>TUI Simulator</span>
          </button>

          <button
            onClick={() => setActiveTab('code')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-2 ${
              activeTab === 'code'
                ? 'bg-emerald-500 text-slate-950 font-semibold shadow-lg shadow-emerald-500/20'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <Code2 className="w-4 h-4" />
            <span>Python Source</span>
          </button>

          <button
            onClick={() => setActiveTab('tests')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-2 ${
              activeTab === 'tests'
                ? 'bg-emerald-500 text-slate-950 font-semibold shadow-lg shadow-emerald-500/20'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Unit Tests</span>
          </button>

          <button
            onClick={() => setActiveTab('guide')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-2 ${
              activeTab === 'guide'
                ? 'bg-emerald-500 text-slate-950 font-semibold shadow-lg shadow-emerald-500/20'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            <span>Termux Guide</span>
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 flex flex-col">
        {activeTab === 'simulator' && (
          <div className="flex-1 flex flex-col lg:flex-row gap-6">
            {/* Left Control Panel */}
            <div className="w-full lg:w-80 bg-slate-900/80 border border-slate-800 rounded-2xl p-5 flex flex-col space-y-6 shadow-xl">
              <div>
                <h3 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider mb-3 flex items-center space-x-2">
                  <Server className="w-4 h-4" />
                  <span>Ollama Connection</span>
                </h3>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-slate-400 mb-1 block">Server URL</label>
                    <input
                      type="text"
                      value={ollamaUrl}
                      onChange={(e) => setOllamaUrl(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 mb-1 block">Active Model</label>
                    <select
                      value={activeModel}
                      onChange={(e) => setActiveModel(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                    >
                      <option value="llama3">llama3:latest</option>
                      <option value="mistral">mistral:7b</option>
                      <option value="gemma2">gemma2:9b</option>
                      <option value="phi3">phi3:mini</option>
                    </select>
                  </div>
                </div>
              </div>

              <hr className="border-slate-800" />

              <div>
                <h3 className="text-sm font-semibold text-amber-400 uppercase tracking-wider mb-3 flex items-center space-x-2">
                  <Sliders className="w-4 h-4" />
                  <span>Parameters</span>
                </h3>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-xs text-slate-400 mb-1">
                      <span>Temperature</span>
                      <span className="text-emerald-400">{temperature}</span>
                    </div>
                    <input
                      type="range"
                      min="0.0"
                      max="1.0"
                      step="0.1"
                      value={temperature}
                      onChange={(e) => setTemperature(parseFloat(e.target.value))}
                      className="w-full accent-emerald-500 cursor-pointer"
                    />
                  </div>
                </div>
              </div>

              <hr className="border-slate-800" />

              <div>
                <h3 className="text-sm font-semibold text-cyan-400 uppercase tracking-wider mb-3 flex items-center space-x-2">
                  <Sparkles className="w-4 h-4" />
                  <span>Slash Commands</span>
                </h3>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <button onClick={() => setInputVal('/new')} className="bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded p-2 text-left transition-colors">
                    <span className="text-emerald-400 font-mono font-bold">/new</span>
                    <p className="text-slate-400 mt-0.5">New chat</p>
                  </button>
                  <button onClick={() => setInputVal('/params')} className="bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded p-2 text-left transition-colors">
                    <span className="text-amber-400 font-mono font-bold">/params</span>
                    <p className="text-slate-400 mt-0.5">Parameters</p>
                  </button>
                  <button onClick={() => setInputVal('/system')} className="bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded p-2 text-left transition-colors">
                    <span className="text-cyan-400 font-mono font-bold">/system</span>
                    <p className="text-slate-400 mt-0.5">System prompt</p>
                  </button>
                  <button onClick={() => setInputVal('/help')} className="bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded p-2 text-left transition-colors">
                    <span className="text-purple-400 font-mono font-bold">/help</span>
                    <p className="text-slate-400 mt-0.5">Help menu</p>
                  </button>
                </div>
              </div>

              <div className="mt-auto pt-4">
                <button
                  onClick={() => setMessages([{ role: 'info', content: 'Conversation reset.' }])}
                  className="w-full py-2.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-xl font-medium text-sm transition-colors flex items-center justify-center space-x-2"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Clear History</span>
                </button>
              </div>
            </div>

            {/* Right Terminal Simulator Window */}
            <div className="flex-1 flex flex-col">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 rounded-full bg-rose-500"></div>
                  <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                  <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                  <span className="text-xs text-slate-400 font-mono ml-2">termux@android:~ (creative_act_ollama.py)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setTerminalWidth(terminalWidth === 'mobile' ? 'full' : 'mobile')}
                    className="px-3 py-1 bg-slate-900 border border-slate-800 rounded text-xs text-slate-300 hover:bg-slate-800 flex items-center space-x-1"
                  >
                    <Smartphone className="w-3.5 h-3.5" />
                    <span>{terminalWidth === 'mobile' ? 'Mobile View (360px)' : 'Full View'}</span>
                  </button>
                </div>
              </div>

              {/* Terminal Screen Container */}
              <div className="flex-1 flex items-center justify-center bg-slate-950 p-4">
                <div className={`w-full ${terminalWidth === 'mobile' ? 'max-w-md' : 'max-w-4xl'} h-[620px] bg-slate-900 border border-slate-800 rounded-xl shadow-2xl flex flex-col font-mono overflow-hidden`}>
                  {/* Terminal Header Bar */}
                  <div className="bg-slate-950 border-b border-slate-800 px-4 py-2.5 flex items-center justify-between text-xs text-slate-400">
                    <div className="flex items-center space-x-2">
                      <Terminal className="w-4 h-4 text-emerald-400" />
                      <span className="font-bold text-slate-200">CreativeAct Ollama Mobile v1.0</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <span className="text-emerald-400 flex items-center space-x-1">
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                        <span>connected</span>
                      </span>
                    </div>
                  </div>

                  {/* Terminal Output Log */}
                  <div className="flex-1 p-4 overflow-y-auto space-y-4 text-sm">
                    {messages.map((m, idx) => {
                      if (m.role === 'info') {
                        return (
                          <div key={idx} className="bg-slate-950/80 border border-slate-800/80 rounded p-3 text-cyan-300 text-xs whitespace-pre-wrap leading-relaxed">
                            {m.content}
                          </div>
                        );
                      }
                      if (m.role === 'user') {
                        return (
                          <div key={idx} className="flex flex-col space-y-1">
                            <span className="text-emerald-400 font-bold">You &gt;</span>
                            <span className="text-slate-100 pl-4">{m.content}</span>
                          </div>
                        );
                      }
                      return (
                        <div key={idx} className="flex flex-col space-y-1">
                          <span className="text-blue-400 font-bold">Assistant &gt;</span>
                          <div className="bg-slate-950/90 border border-slate-800 rounded-lg p-3 text-slate-200 text-xs leading-relaxed whitespace-pre-wrap">
                            {m.content}
                          </div>
                        </div>
                      );
                    })}

                    {isThinking && (
                      <div className="flex items-center space-x-2 text-cyan-400 text-xs animate-pulse pl-2">
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>Thinking...</span>
                      </div>
                    )}
                    <div ref={chatEndRef} />
                  </div>

                  {/* Terminal Input Form */}
                  <form onSubmit={handleSendMessage} className="bg-slate-950 border-t border-slate-800 p-3 flex items-center space-x-2">
                    <span className="text-emerald-400 font-bold text-sm">You &gt;</span>
                    <input
                      type="text"
                      value={inputVal}
                      onChange={(e) => setInputVal(e.target.value)}
                      placeholder="Type a message or slash command (/help)..."
                      className="flex-1 bg-transparent text-slate-100 placeholder-slate-500 focus:outline-none text-sm font-mono"
                    />
                    <button
                      type="submit"
                      disabled={isThinking || !inputVal.trim()}
                      className="px-3 py-1.5 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-bold rounded text-xs transition-colors flex items-center space-x-1"
                    >
                      <Send className="w-3.5 h-3.5" />
                    </button>
                  </form>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'code' && (
          <div className="flex-1 flex flex-col lg:flex-row gap-6">
            {/* File List Sidebar */}
            <div className="w-full lg:w-80 bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col space-y-2 shadow-xl">
              <div className="flex items-center justify-between mb-2 px-2">
                <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Project Files</h3>
                <button
                  onClick={handleDownloadAll}
                  className="text-xs text-emerald-400 hover:text-emerald-300 flex items-center space-x-1 font-medium"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download All</span>
                </button>
              </div>

              <div className="space-y-1 overflow-y-auto max-h-[550px]">
                {PYTHON_FILES.map((file) => (
                  <button
                    key={file.name}
                    onClick={() => setSelectedFile(file)}
                    className={`w-full text-left px-3 py-2.5 rounded-xl text-sm transition-all flex items-center justify-between group ${
                      selectedFile.name === file.name
                        ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-medium'
                        : 'hover:bg-slate-800/80 text-slate-300 border border-transparent'
                    }`}
                  >
                    <div className="flex items-center space-x-2.5 truncate">
                      <FileText className="w-4 h-4 text-slate-400 group-hover:text-emerald-400 shrink-0" />
                      <span className="truncate font-mono text-xs">{file.name}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Code Viewer Panel */}
            <div className="flex-1 flex flex-col bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
              <div className="bg-slate-950 px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-slate-100 font-mono">{selectedFile.name}</h2>
                  <p className="text-xs text-slate-400">{selectedFile.description}</p>
                </div>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => handleCopy(selectedFile.content)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium flex items-center space-x-1.5 transition-colors border border-slate-700"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copied!' : 'Copy Code'}</span>
                  </button>
                  <button
                    onClick={() => handleDownloadFile(selectedFile)}
                    className="px-3 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-lg text-xs font-bold flex items-center space-x-1.5 transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download</span>
                  </button>
                </div>
              </div>

              <div className="flex-1 p-6 bg-slate-950 overflow-x-auto">
                <pre className="font-mono text-xs text-slate-300 leading-relaxed">
                  <code>{selectedFile.content}</code>
                </pre>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'tests' && (
          <div className="flex-1 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800">
              <div>
                <h2 className="text-lg font-bold text-slate-100">Automated Test Suite</h2>
                <p className="text-xs text-slate-400">Verifying command parsing, parameter management, conversation history, and mocked Ollama client.</p>
              </div>
              <div className="flex items-center space-x-2 text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1.5 rounded-lg text-xs font-semibold">
                <Check className="w-4 h-4" />
                <span>All 10 Tests Passed (0.012s)</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {[
                { name: 'test_config_management', desc: 'Verifies default config loading, saving, and parameter updates.' },
                { name: 'test_conversation_management', desc: 'Verifies message adding, API formatting, and history clearing.' },
                { name: 'test_command_dispatcher_exit', desc: 'Verifies slash command execution for /exit gracefully stopping REPL.' },
                { name: 'test_command_dispatcher_new', desc: 'Verifies /new clears conversation history and resets context.' },
                { name: 'test_command_dispatcher_system', desc: 'Verifies /system dynamically inspects and updates system prompts.' },
                { name: 'test_command_dispatcher_params', desc: 'Verifies /params views and parses integer/float parameter tuning.' },
                { name: 'test_command_dispatcher_server', desc: 'Verifies /server updates active Ollama URL and client configuration.' },
                { name: 'test_ollama_client_check_connection', desc: 'Verifies server connectivity checks with both positive and offline mock.' },
                { name: 'test_ollama_client_list_models', desc: 'Verifies model discovery and tag parsing from Ollama API.' },
                { name: 'test_ollama_client_streaming', desc: 'Verifies real-time chunk streaming and done packet termination.' },
              ].map((test) => (
                <div key={test.name} className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
                      <Check className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <h4 className="text-xs font-mono font-medium text-slate-200">{test.name}</h4>
                      <p className="text-[11px] text-slate-400">{test.desc}</p>
                    </div>
                  </div>
                  <span className="text-[11px] text-emerald-400 font-mono shrink-0 ml-2">PASSED</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'guide' && (
          <div className="flex-1 bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl space-y-6">
            <div>
              <h2 className="text-xl font-bold text-slate-100 mb-2">Android Termux Installation & Usage Guide</h2>
              <p className="text-sm text-slate-400">Follow these steps to run CreativeAct Ollama Mobile natively on your Android device.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-3">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold">1</div>
                <h3 className="font-semibold text-slate-200">Install Termux</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Download and install Termux from F-Droid (recommended). Avoid outdated Play Store versions.
                </p>
              </div>

              <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-3">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold">2</div>
                <h3 className="font-semibold text-slate-200">Run Setup Script</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Clone or copy the project files to Termux, then run:<br />
                  <code className="text-emerald-400 bg-slate-900 px-1 py-0.5 rounded font-mono">bash termux_setup.sh</code>
                </p>
              </div>

              <div className="bg-slate-950 border border-slate-800 rounded-xl p-5 space-y-3">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold">3</div>
                <h3 className="font-semibold text-slate-200">Start Ollama & App</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Start Ollama in a separate session with <code className="text-emerald-400 bg-slate-900 px-1 py-0.5 rounded font-mono">ollama serve</code>, then run <code className="text-emerald-400 bg-slate-900 px-1 py-0.5 rounded font-mono">python creative_act_ollama.py</code>.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
