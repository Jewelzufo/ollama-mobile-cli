"""
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
            return false

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
        """
        Stream chat completion from Ollama API.
        Yields chunks of text as they arrive.
        """
        url = f"{self.base_url}/api/chat"
        
        payload_messages = list(messages)
        if system:
            # Prepend system prompt if provided
            payload_messages.insert(0, {"role": "system", "content": system})

        payload: Dict[str, Any] = {
            "model": model,
            "messages": payload_messages,
            "stream": True
        }
        
        if options:
            payload["options"] = options

        try:
            with requests.post(url, json=payload, stream=True, timeout=self.timeout) as response:
                if response.status_code != 200:
                    error_msg = response.text
                    try:
                        err_json = response.json()
                        error_msg = err_json.get("error", error_msg)
                    except Exception:
                        pass
                    raise RuntimeError(f"Ollama API Error ({response.status_code}): {error_msg}")

                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode("utf-8"))
                            message = chunk.get("message", {})
                            content = message.get("content", "")
                            if content:
                                yield content
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except requests.Timeout:
            raise TimeoutError("Ollama request timed out. The model might be loading or the server is unresponsive.")
        except requests.RequestException as e:
            raise ConnectionError(f"Network error communicating with Ollama: {e}")
