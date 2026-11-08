"""
CreativeAct Ollama Mobile - Conversation Manager
Manages chat history, message logs, and persistence.
"""

import os
import json
from typing import List, Dict, Any
from datetime import datetime

class ConversationManager:
    def __init__(self, history_path: str = None):
        if history_path is None:
            home = os.path.expanduser("~")
            history_dir = os.path.join(home, ".config", "creative_act_ollama")
            os.makedirs(history_dir, exist_ok=True)
            self.history_path = os.path.join(history_dir, "history.json")
        else:
            self.history_path = history_path
            os.makedirs(os.path.dirname(os.path.abspath(self.history_path)), exist_ok=True)
            
        self.messages: List[Dict[str, str]] = []
        self.load_history()

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the current conversation."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.save_history()

    def get_api_messages(self) -> List[Dict[str, str]]:
        """Return messages in format expected by Ollama API (role & content only)."""
        return [{"role": m["role"], "content": m["content"]} for m in self.messages]

    def clear(self) -> None:
        """Clear current conversation history."""
        self.messages = []
        self.save_history()

    def save_history(self) -> bool:
        """Persist conversation history to disk."""
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(self.messages, f, indent=2)
            return True
        except Exception:
            return False

    def load_history(self) -> None:
        """Load conversation history from disk."""
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.messages = data
            except Exception:
                self.messages = []
