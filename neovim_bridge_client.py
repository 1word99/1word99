# osmanli_ai/utils/interprocess/neovim_bridge_client.py
import asyncio
import json
from typing import Any, Dict

from loguru import logger

from osmanli_ai.core.exceptions import NeovimBridgeError


class NeovimBridgeClient:
    def __init__(self, host="127.0.0.1", port=8001, message_handler=None):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.message_handler = message_handler
        self._listen_task = None
        logger.info(f"NeovimBridgeClient initialized for {host}:{port}")

    async def connect(self):
        """Attempts to establish an asynchronous connection to the Neovim bridge server."""
        if self.reader and self.writer:  # Already connected
            return True
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port
            )
            logger.info("Connected to Neovim bridge server.")
            if self.message_handler:
                self._listen_task = asyncio.create_task(self._listen_for_messages())
            return True
        except ConnectionRefusedError:
            logger.warning(
                f"Connection refused by Neovim bridge server at {self.host}:{self.port}. Please ensure the Neovim bridge is running and accessible."
            )
            self.reader = None
            self.writer = None
            return False
        except asyncio.TimeoutError:
            logger.warning(
                f"Connection to Neovim bridge server timed out at {self.host}:{self.port}."
            )
            self.reader = None
            self.writer = None
            return False
        except Exception as e:
            logger.error(f"Error connecting to Neovim bridge: {e}", exc_info=True)
            self.reader = None
            self.writer = None
            raise NeovimBridgeError(f"Error connecting to Neovim bridge: {e}") from e

    def register_message_handler(self, handler):
        """Registers a handler for incoming messages."""
        self.message_handler = handler
        if self.is_connected() and not self._listen_task:
            self._listen_task = asyncio.create_task(self._listen_for_messages())

    def is_connected(self) -> bool:
        """Checks if the client is currently connected to the server."""
        return self.reader is not None and self.writer is not None

    async def send_notification(self, message: Dict[str, Any]):
        """Sends a JSON notification to Neovim bridge without expecting a response."""
        if not self.is_connected():
            logger.warning("Not connected to Neovim bridge. Cannot send notification.")
            raise NeovimBridgeError(
                "Not connected to Neovim bridge. Cannot send notification."
            )
        try:
            json_message = json.dumps(message).encode("utf-8") + b"\n"
            self.writer.write(json_message)
            await self.writer.drain()
            logger.debug(f"Sent notification to Neovim: {message}")
        except Exception as e:
            logger.error(
                f"Error sending notification to Neovim bridge: {e}", exc_info=True
            )
            self.disconnect()
            raise NeovimBridgeError(
                f"Error sending notification to Neovim bridge: {e}"
            ) from e

    async def send_request(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Sends a JSON request to Neovim bridge and waits for a JSON response."""
        if not self.is_connected():
            logger.warning("Not connected to Neovim bridge. Cannot send request.")
            raise NeovimBridgeError(
                "Not connected to Neovim bridge. Cannot send request."
            )
        try:
            json_message = json.dumps(message).encode("utf-8") + b"\n"
            self.writer.write(json_message)
            await self.writer.drain()
            logger.debug(f"Sent request to Neovim: {message}")

            if message.get("type") == "get_diagnostics":
                response_data = await self.reader.readuntil(b"\n")
                response_json = json.loads(response_data.decode("utf-8"))
                logger.debug(f"Received response from Neovim: {response_json}")
                return response_json
            else:
                # For other request types, you might have a different response protocol
                return {}

        except Exception as e:
            logger.error(
                f"Error sending/receiving request from Neovim bridge: {e}",
                exc_info=True,
            )
            self.disconnect()
            raise NeovimBridgeError(
                f"Error sending/receiving request from Neovim bridge: {e}"
            ) from e

    async def _listen_for_messages(self):
        """Continuously listens for messages from the Neovim bridge server."""
        while self.is_connected():
            try:
                data = await self.reader.readuntil(b"\n")
                message = json.loads(data.decode("utf-8"))
                logger.debug(f"Received message from Neovim: {message}")
                if self.message_handler:
                    await self.message_handler(message)
            except asyncio.IncompleteReadError:
                logger.info("Server disconnected.")
                break
            except Exception as e:
                logger.error(f"Error receiving message from Neovim: {e}", exc_info=True)
                break
        self.disconnect()

    def disconnect(self):
        """Closes the connection to the Neovim bridge server."""
        if self._listen_task:
            self._listen_task.cancel()
            self._listen_task = None
        if self.writer:
            self.writer.close()
            self.reader = None
            self.writer = None
            logger.info("Disconnected from Neovim bridge server.")

    async def self_test(self) -> bool:
        """Performs a self-test of the NeovimBridgeClient component.
        This test will attempt to connect to the configured Neovim bridge.
        Returns True if the component can connect, False otherwise.
        """
        logger.info("Running self-test for NeovimBridgeClient...")
        try:
            if await self.connect():
                logger.info(
                    "NeovimBridgeClient self-test passed: Connection successful."
                )
                self.disconnect()
                return True
            else:
                logger.error(
                    "NeovimBridgeClient self-test failed: Could not connect to bridge."
                )
                return False
        except Exception as e:
            logger.error(f"NeovimBridgeClient self-test failed: {e}")
            raise NeovimBridgeError(f"NeovimBridgeClient self-test failed: {e}") from e
