"""
CreativeAct Ollama Mobile - Ollama API Client
Handles communication with Ollama HTTP API (models list, generate, chat with streaming).
Provides fallback to standard library urllib if requests is not installed,
and supports both /api/chat and /api/generate fallback for non-template models.
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
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 45):
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
        Attempts /api/chat first. If the model does not support chat templates,
        seamlessly falls back to /api/generate.
        Yields chunks of text as they arrive.
        """
        url = f"{self.base_url}/api/chat"

        payload_messages = []
        if system:
            payload_messages.append({"role": "system", "content": system})
        payload_messages.extend(messages)

        payload: Dict[str, Any] = {
            "model": model,
            "messages": payload_messages,
            "stream": True
        }

        # Clean options to ensure valid Ollama format
        if options:
            clean_opts = {k: v for k, v in options.items() if v is not None}
            if clean_opts:
                payload["options"] = clean_opts

        json_bytes = json.dumps(payload).encode("utf-8")

        if HAS_REQUESTS:
            try:
                response = requests.post(url, json=payload, stream=True, timeout=self.timeout)
                
                # Check if model rejects chat format (e.g. base/generate model or template error)
                if response.status_code != 200:
                    err_msg = response.text
                    try:
                        err_json = response.json()
                        err_msg = err_json.get("error", err_msg)
                    except Exception:
                        pass

                    # If model does not support chat or 400/404, fall back to /api/generate
                    if response.status_code in (400, 404) or any(w in err_msg.lower() for w in ["template", "chat", "does not support", "system"]):
                        yield from self._generate_stream_fallback(model, messages, options, system)
                        return
                    else:
                        raise RuntimeError(f"Ollama API Error ({response.status_code}): {err_msg}")

                with response:
                    for line in response.iter_lines():
                        if not line:
                            continue
                        if isinstance(line, bytes):
                            line_str = line.decode("utf-8", errors="replace").strip()
                        else:
                            line_str = str(line).strip()
                        if not line_str:
                            continue

                        try:
                            chunk = json.loads(line_str)
                        except json.JSONDecodeError:
                            continue

                        content = ""
                        if "message" in chunk and isinstance(chunk["message"], dict):
                            content = chunk["message"].get("content", "")
                        if not content and "response" in chunk:
                            content = chunk.get("response", "")

                        if content:
                            yield content

                        if chunk.get("done", False):
                            break

            except requests.Timeout:
                raise TimeoutError("Ollama request timed out. Model might still be loading into RAM/VRAM.")
            except requests.RequestException as e:
                raise ConnectionError(f"Network error communicating with Ollama: {e}")

        else:
            # Standard library urllib implementation
            try:
                req = urllib.request.Request(
                    url,
                    data=json_bytes,
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                try:
                    response = urllib.request.urlopen(req, timeout=self.timeout)
                except urllib.error.HTTPError as e:
                    err_body = e.read().decode("utf-8", errors="replace")
                    try:
                        err_json = json.loads(err_body)
                        err_msg = err_json.get("error", err_body)
                    except Exception:
                        err_msg = err_body
                    
                    if e.code in (400, 404) or any(w in err_msg.lower() for w in ["template", "chat", "does not support", "system"]):
                        yield from self._generate_stream_fallback(model, messages, options, system)
                        return
                    else:
                        raise RuntimeError(f"Ollama API Error ({e.code}): {err_msg}")

                with response:
                    while True:
                        line = response.readline()
                        if not line:
                            break
                        line_str = line.decode("utf-8", errors="replace").strip()
                        if not line_str:
                            continue

                        try:
                            chunk = json.loads(line_str)
                        except json.JSONDecodeError:
                            continue

                        content = ""
                        if "message" in chunk and isinstance(chunk["message"], dict):
                            content = chunk["message"].get("content", "")
                        if not content and "response" in chunk:
                            content = chunk.get("response", "")

                        if content:
                            yield content

                        if chunk.get("done", False):
                            break

            except Exception as e:
                raise ConnectionError(f"Network error communicating with Ollama: {e}")

    def _generate_stream_fallback(
        self,
        model: str,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None,
        system: Optional[str] = None
    ) -> Generator[str, None, None]:
        """Fallback to /api/generate for models without explicit chat template."""
        url = f"{self.base_url}/api/generate"

        prompt_lines = []
        if system:
            prompt_lines.append(f"System: {system}\n")
        for m in messages:
            role = "User" if m["role"] == "user" else "Assistant"
            prompt_lines.append(f"{role}: {m['content']}")
        prompt_lines.append("Assistant:")
        full_prompt = "\n".join(prompt_lines)

        payload: Dict[str, Any] = {
            "model": model,
            "prompt": full_prompt,
            "stream": True
        }
        if options:
            clean_opts = {k: v for k, v in options.items() if v is not None}
            if clean_opts:
                payload["options"] = clean_opts

        json_bytes = json.dumps(payload).encode("utf-8")

        if HAS_REQUESTS:
            try:
                with requests.post(url, json=payload, stream=True, timeout=self.timeout) as response:
                    if response.status_code != 200:
                        raise RuntimeError(f"Ollama Generate API Error ({response.status_code}): {response.text}")

                    for line in response.iter_lines():
                        if not line:
                            continue
                        line_str = line.decode("utf-8", errors="replace").strip() if isinstance(line, bytes) else str(line).strip()
                        if not line_str:
                            continue
                        try:
                            chunk = json.loads(line_str)
                            content = chunk.get("response", "")
                            if content:
                                yield content
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                raise ConnectionError(f"Ollama generate fallback error: {e}")
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
                        line_str = line.decode("utf-8", errors="replace").strip()
                        if not line_str:
                            continue
                        try:
                            chunk = json.loads(line_str)
                            content = chunk.get("response", "")
                            if content:
                                yield content
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                raise ConnectionError(f"Ollama generate fallback error: {e}")
