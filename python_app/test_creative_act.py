"""
CreativeAct Ollama Mobile - Unit Test Suite
Tests configuration, conversation history, command parsing, and Ollama client with mocked responses.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
import json

from config import ConfigManager
from conversation import ConversationManager
from ollama_client import OllamaClient
from commands import CommandDispatcher

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

        # Test parameter update
        self.assertTrue(self.config.update_parameter("temperature", 0.5))
        self.assertEqual(self.config.get("parameters")["temperature"], 0.5)
        self.assertFalse(self.config.update_parameter("non_existent", 1.0))

    def test_conversation_management(self):
        self.assertEqual(len(self.conversation.messages), 0)
        self.conversation.add_message("user", "Hello Ollama")
        self.assertEqual(len(self.conversation.messages), 1)
        self.assertEqual(self.conversation.messages[0]["role"], "user")
        self.assertEqual(self.conversation.messages[0]["content"], "Hello Ollama")

        api_msgs = self.conversation.get_api_messages()
        self.assertEqual(len(api_msgs), 1)
        self.assertEqual(api_msgs[0], {"role": "user", "content": "Hello Ollama"})

        self.conversation.clear()
        self.assertEqual(len(self.conversation.messages), 0)

    @patch("requests.get")
    def test_ollama_connection_and_models(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "llama3:latest"}, {"name": "gemma:7b"}]
        }
        mock_get.return_value = mock_response

        self.assertTrue(self.client.check_connection())
        models = self.client.list_models()
        self.assertEqual(models, ["llama3:latest", "gemma:7b"])

    def test_command_dispatcher_exit(self):
        should_exit = self.dispatcher.handle_command("/exit")
        self.assertTrue(should_exit)

    def test_command_dispatcher_system(self):
        self.dispatcher.handle_command("/system You are an expert Python coding assistant.")
        self.assertEqual(self.config.get("system_prompt"), "You are an expert Python coding assistant.")

    def test_command_dispatcher_params(self):
        self.dispatcher.handle_command("/params temperature 0.2")
        self.assertEqual(self.config.get("parameters")["temperature"], 0.2)

if __name__ == "__main__":
    unittest.main()
