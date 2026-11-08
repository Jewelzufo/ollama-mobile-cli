"""
CreativeAct Ollama Mobile - Ollama API Client
Handles communication with Ollama HTTP API (models list, generate, chat with streaming).
Provides fallback to standard library urllib if requests is not installed.
"""

import json
from typing import Generator, Dict, Any, List, Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def check_connection(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            if HAS_REQUESTS:
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                return response.status_code == 200
            else:
                req = urllib.request.Request(f"{self.base_url}/api/tags")
                with urllib.request.urlopen(req, timeout=5) as response:
                    return response.status == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """Fetch list of available models from Ollama."""
        try:
            if HAS_REQUESTS:
                response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    return [m.get("name") for m in models if "name" in m]
                return []
            else:
                req = urllib.request.Request(f"{self.base_url}/api/tags")
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    models = data.get("models", [])
                    return [m.get("name") for m in models if "name" in m]
        except Exception as e:
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
            payload_messages.insert(0, {"role": "system", "content": system})

        payload: Dict[str, Any] = {
            "model": model,
            "messages": payload_messages,
            "stream": True
        }
        
        if options:
            payload["options"] = options

        json_bytes = json.dumps(payload).encode("utf-8")

        if HAS_REQUESTS:
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
                raise TimeoutError("Ollama request timed out.")
            except requests.RequestException as e:
                raise ConnectionError(f"Network error communicating with Ollama: {e}")
        else:
            try:
                req = urllib.request.Request(
                    url,
                    data=json_bytes,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    while True:
                        line = response.readline()
                        if not line:
                            break
                        line_str = line.decode("utf-8").strip()
                        if line_str:
                            try:
                                chunk = json.loads(line_str)
                                message = chunk.get("message", {})
                                content = message.get("content", "")
                                if content:
                                    yield content
                                if chunk.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                raise ConnectionError(f"Network error communicating with Ollama: {e}")
