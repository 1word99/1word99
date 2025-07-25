import sys
from unittest.mock import MagicMock
import pytest

sys.path.append(".")

from osmanli_ai.core.dispatcher import RequestDispatcher


class TestRequestDispatcher:
    @pytest.mark.asyncio
    async def test_multilink_functionality(self):
        # Create a mock assistant instance
        assistant_mock = MagicMock()
        assistant_mock.memory.get_history.return_value = []
        assistant_mock.plugins.get_plugin.return_value = None
        assistant_mock.quran = None
        assistant_mock.neovim_bridge_client.connect.return_value = False

        # Create a RequestDispatcher instance
        dispatcher = RequestDispatcher(assistant_mock)

        # Define a multilink query
        query = "hello; what is your name"

        # Call the route method
        response = await dispatcher.route(query, {})

        # Assert that the response contains the expected greetings
        assert "Greetings, seeker of knowledge!" in response
        assert "I am Osmanli AI, your dedicated assistant." in response
