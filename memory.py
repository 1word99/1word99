# osmanli_ai/core/memory.py
from datetime import datetime
from typing import Any, Dict, List

from loguru import logger


class ConversationMemory:
    """
    Manages the conversation history for the AI assistant, including adding, retrieving,
    and clearing messages, and maintaining a maximum history length.
    """

    def __init__(self, max_history_length: int = 50):
        """Initializes the ConversationMemory.

        Args:
            max_history_length (int): The maximum number of messages to store in history.
        """
        self.history: List[Dict[str, Any]] = []
        self.max_history_length = max_history_length
        self.session_start_time = datetime.now()
        logger.info("ConversationMemory initialized.")

    def add_message(self, role: str, content: str, timestamp: datetime = None):
        """Adds a message to the conversation history.

        Args:
            role (str): The role of the message sender (e.g., "user", "assistant", "system").
            content (str): The content of the message.
            timestamp (datetime, optional): The timestamp of the message. Defaults to now.
        """
        if timestamp is None:
            timestamp = datetime.now()
        message = {
            "role": role,
            "content": content,
            "timestamp": timestamp.isoformat(),
        }
        self.history.append(message)
        if len(self.history) > self.max_history_length:
            self.history.pop(0)
        logger.debug("Message added: %s: %s...", role, content[:50])

    def add_user_message(self, content: str):
        """Adds a user message to history."

        Args:
            content (str): The content of the user message.
        """
        self.add_message("user", content)

    def add_assistant_message(self, content: str):
        """Adds an assistant message to history."

        Args:
            content (str): The content of the assistant message.
        """
        self.add_message("assistant", content)

    def add_system_message(self, content: str):
        """Adds a system message to history."

        Args:
            content (str): The content of the system message.
        """
        self.add_message("system", content)

    def get_history(self, num_messages: int = -1) -> List[Dict[str, Any]]:
        """
        Retrieves a portion of the conversation history.
        Args:
            num_messages (int): The number of most recent messages to retrieve.
                                -1 to retrieve all.
        Returns:
            List[Dict[str, Any]]: A list of message dictionaries.
        """
        if num_messages == -1:
            return list(self.history)
        return list(self.history[-num_messages:])

    def get_full_context_text(self, num_messages: int = -1) -> str:
        """
        Returns the conversation history as a single string, suitable for LLM context.

        Args:
            num_messages (int): The number of most recent messages to retrieve.
                                -1 to retrieve all.

        Returns:
            str: A string representation of the conversation history.
        """
        context_str = ""
        for msg in self.get_history(num_messages):
            context_str += f"{msg['role'].capitalize()}: {msg['content']}\n"
        return context_str.strip()

    def clear_history(self):
        """Clears the entire conversation history." """
        self.history = []
        self.session_start_time = datetime.now()
        logger.info("Conversation history cleared.")

    def get_session_duration(self) -> float:
        """Returns the duration of the current conversation session in seconds."

        Returns:
            float: The duration of the current conversation session in seconds.
        """
        return (datetime.now() - self.session_start_time).total_seconds()

    def self_test(self) -> bool:
        """Performs a self-test of the ConversationMemory component.
        Returns True if the component is healthy, False otherwise.
        """
        logger.info("Running self-test for ConversationMemory...")
        try:
            # Test message addition and retrieval
            initial_history_len = len(self.history)
            self.add_user_message("Hello")
            self.add_assistant_message("Hi there!")
            if len(self.history) != initial_history_len + 2:
                logger.error("Memory self-test failed: Message addition failed.")
                return False

            # Test get_history
            last_message = self.get_history(1)[0]
            if (
                last_message["role"] != "assistant"
                or last_message["content"] != "Hi there!"
            ):
                logger.error("Memory self-test failed: get_history failed.")
                return False

            # Test get_full_context_text
            context_text = self.get_full_context_text(2)
            if (
                "User: Hello" not in context_text
                or "Assistant: Hi there!" not in context_text
            ):
                logger.error("Memory self-test failed: get_full_context_text failed.")
                return False

            # Test clear_history
            self.clear_history()
            if len(self.history) != 0:
                logger.error("Memory self-test failed: clear_history failed.")
                return False

            logger.info("ConversationMemory self-test passed.")
            return True
        except Exception as e:
            logger.error(f"ConversationMemory self-test failed: {e}")
            return False
