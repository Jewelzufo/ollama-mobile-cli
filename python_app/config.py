"""
CreativeAct Ollama Mobile - Configuration Manager
Handles loading, saving, and managing app settings and persistent state.
"""

import os
import json
from typing import Dict, Any

DEFAULT_CONFIG: Dict[str, Any] = {
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
    },
    "display": {
        "syntax_theme": "monokai",
        "show_line_numbers": False,
        "markdown_width": 76
    }
}

class ConfigManager:
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to ~/.config/creative_act_ollama/config.json
            home = os.path.expanduser("~")
            config_dir = os.path.join(home, ".config", "creative_act_ollama")
            os.makedirs(config_dir, exist_ok=True)
            self.config_path = os.path.join(config_dir, "config.json")
        else:
            self.config_path = config_path
            os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
            
        self.config = self.load()

    def load(self) -> Dict[str, Any]:
        """Load configuration from disk, falling back to defaults."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Merge with default config to ensure all keys exist
                    config = dict(DEFAULT_CONFIG)
                    for k, v in data.items():
                        if isinstance(v, dict) and k in config and isinstance(config[k], dict):
                            config[k].update(v)
                        else:
                            config[k] = v
                    return config
            except Exception:
                return dict(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)

    def save(self) -> bool:
        """Save current configuration to disk."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception:
            return False

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.config[key] = value
        self.save()

    def update_parameter(self, param_name: str, value: Any) -> bool:
        if "parameters" in self.config and param_name in self.config["parameters"]:
            self.config["parameters"][param_name] = value
            self.save()
            return True
        return False
