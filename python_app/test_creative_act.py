"""
CreativeAct Ollama Mobile - Comprehensive Unit Test Suite
Tests configuration, conversation history, command parsing, parameter updates,
Ollama client with mocked streaming responses, fallback to /api/generate,
and error handling.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
import json

from config import ConfigManager
from conversation import ConversationManager
from ollama_client import OllamaClient, HAS_REQUESTS
from commands import CommandDispatcher
from ui import TerminalUI, console

class TestCreativeActOllama(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.test_dir.name, "config.json")
        self.history_path = os.path.join(self.test_dir.name, "history.json")

        self.config = ConfigManager(self.config_path)
        self.conversation = ConversationManager(self.history_path)
        self.client = OllamaClient(base_url="http://localhost:11434")
        self.dispatcher = CommandDispatcher(self.config, self.conversation, self.client)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_config_management(self):
        self.assertEqual(self.config.get("model"), "llama3")
        self.config.set("model", "mistral")
        self.assertEqual(self.config.get("model"), "mistral")

        self.assertTrue(self.config.update_parameter("temperature", 0.5))
        self.assertEqual(self.config.get("parameters")["temperature"], 0.5)
        self.assertFalse(self.config.update_parameter("non_existent", 1.0))

        new_config_instance = ConfigManager(self.config_path)
        self.assertEqual(new_config_instance.get("model"), "mistral")
        self.assertEqual(new_config_instance.get("parameters")["temperature"], 0.5)

    def test_conversation_management(self):
        self.assertEqual(len(self.conversation.messages), 0)
        self.conversation.add_message("user", "Hello Ollama")
        self.assertEqual(len(self.conversation.messages), 1)
        self.assertEqual(self.conversation.messages[0]["role"], "user")
        self.assertEqual(self.conversation.messages[0]["content"], "Hello Ollama")

        api_msgs = self.conversation.get_api_messages()
        self.assertEqual(len(api_msgs), 1)
        self.assertEqual(api_msgs[0], {"role": "user", "content": "Hello Ollama"})

        new_conv = ConversationManager(self.history_path)
        self.assertEqual(len(new_conv.messages), 1)
        self.assertEqual(new_conv.messages[0]["content"], "Hello Ollama")

        self.conversation.clear()
        self.assertEqual(len(self.conversation.messages), 0)

    def test_command_dispatcher_exit(self):
        should_exit = self.dispatcher.handle_command("/exit")
        self.assertTrue(should_exit)

    def test_command_dispatcher_new(self):
        self.conversation.add_message("user", "Initial message")
        self.assertEqual(len(self.conversation.messages), 1)
        should_exit = self.dispatcher.handle_command("/new")
        self.assertFalse(should_exit)
        self.assertEqual(len(self.conversation.messages), 0)

    def test_command_dispatcher_system(self):
        self.dispatcher.handle_command("/system You are an expert Python assistant.")
        self.assertEqual(self.config.get("system_prompt"), "You are an expert Python assistant.")

    def test_command_dispatcher_params(self):
        self.dispatcher.handle_command("/params temperature 0.2")
        self.assertEqual(self.config.get("parameters")["temperature"], 0.2)
        self.dispatcher.handle_command("/params top_k 50")
        self.assertEqual(self.config.get("parameters")["top_k"], 50)

    def test_command_dispatcher_server(self):
        self.dispatcher.handle_command("/server http://192.168.1.100:11434")
        self.assertEqual(self.config.get("ollama_url"), "http://192.168.1.100:11434")
        self.assertEqual(self.client.base_url, "http://192.168.1.100:11434")

    def test_ollama_client_check_connection(self):
        if HAS_REQUESTS:
            with patch("requests.get") as mock_get:
                mock_get.return_value.status_code = 200
                self.assertTrue(self.client.check_connection())

                mock_get.side_effect = Exception("Connection refused")
                self.assertFalse(self.client.check_connection())
        else:
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_cm = MagicMock()
                mock_cm.status = 200
                mock_cm.__enter__.return_value = mock_cm
                mock_urlopen.return_value = mock_cm
                self.assertTrue(self.client.check_connection())

                mock_urlopen.side_effect = Exception("Connection refused")
                self.assertFalse(self.client.check_connection())

    def test_ollama_client_list_models(self):
        mock_data = {"models": [{"name": "lfm2.5-350m:latest"}, {"name": "llama3:latest"}]}
        if HAS_REQUESTS:
            with patch("requests.get") as mock_get:
                mock_get.return_value.status_code = 200
                mock_get.return_value.json.return_value = mock_data
                models = self.client.list_models()
                self.assertEqual(models, ["lfm2.5-350m:latest", "llama3:latest"])
        else:
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_cm = MagicMock()
                mock_cm.status = 200
                mock_cm.read.return_value = json.dumps(mock_data).encode("utf-8")
                mock_cm.__enter__.return_value = mock_cm
                mock_urlopen.return_value = mock_cm
                models = self.client.list_models()
                self.assertEqual(models, ["lfm2.5-350m:latest", "llama3:latest"])

    def test_ollama_client_streaming_chat(self):
        chunk1 = json.dumps({"message": {"content": "Hello "}, "done": False})
        chunk2 = json.dumps({"message": {"content": "World!"}, "done": True})

        if HAS_REQUESTS:
            with patch("requests.post") as mock_post:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.iter_lines.return_value = [chunk1.encode("utf-8"), chunk2.encode("utf-8")]
                mock_resp.__enter__.return_value = mock_resp
                mock_post.return_value = mock_resp

                chunks = list(self.client.chat_stream("lfm2.5-350m:latest", [{"role": "user", "content": "hi"}]))
                self.assertEqual(chunks, ["Hello ", "World!"])
        else:
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_cm = MagicMock()
                mock_cm.status = 200
                lines = [chunk1.encode("utf-8") + b"\n", chunk2.encode("utf-8") + b"\n", b""]
                mock_cm.readline.side_effect = lines
                mock_cm.__enter__.return_value = mock_cm
                mock_urlopen.return_value = mock_cm

                chunks = list(self.client.chat_stream("lfm2.5-350m:latest", [{"role": "user", "content": "hi"}]))
                self.assertEqual(chunks, ["Hello ", "World!"])

    def test_ollama_client_fallback_to_generate(self):
        """Test fallback when model does not support /api/chat template."""
        chunk1 = json.dumps({"response": "Fallback response token", "done": True})

        if HAS_REQUESTS:
            with patch("requests.post") as mock_post:
                # First call to /api/chat returns 400 template error
                err_resp = MagicMock()
                err_resp.status_code = 400
                err_resp.text = json.dumps({"error": "model does not support chat"})
                err_resp.json.return_value = {"error": "model does not support chat"}

                # Second call to /api/generate succeeds
                ok_resp = MagicMock()
                ok_resp.status_code = 200
                ok_resp.iter_lines.return_value = [chunk1.encode("utf-8")]
                ok_resp.__enter__.return_value = ok_resp

                mock_post.side_effect = [err_resp, ok_resp]

                chunks = list(self.client.chat_stream("lfm2.5-350m:latest", [{"role": "user", "content": "hi"}]))
                self.assertEqual(chunks, ["Fallback response token"])
        else:
            with patch("urllib.request.urlopen") as mock_urlopen:
                # Fallback mock for urllib
                mock_cm = MagicMock()
                mock_cm.status = 200
                mock_cm.readline.side_effect = [chunk1.encode("utf-8") + b"\n", b""]
                mock_cm.__enter__.return_value = mock_cm
                mock_urlopen.return_value = mock_cm

                # Test _generate_stream_fallback directly
                chunks = list(self.client._generate_stream_fallback("lfm2.5-350m:latest", [{"role": "user", "content": "hi"}]))
                self.assertEqual(chunks, ["Fallback response token"])

    def test_status_start_and_stop(self):
        """Verify status indicator start and stop lifecycle."""
        status = console.status("Test status")
        status.start()
        status.stop()

    def test_markdown_rendering(self):
        """Verify markdown rendering function execution."""
        TerminalUI.print_markdown("### Heading\n**bold text**\n```python\nprint(1)\n```")

if __name__ == "__main__":
    unittest.main()
