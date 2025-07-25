# osmanli_ai/utils/interprocess/neovim_bridge_server.py
import json
import socket
import threading
import asyncio
import time  # Added for time.sleep in heartbeats

from loguru import logger

from osmanli_ai.core.exceptions import NeovimBridgeError


class NeovimBridge:
    """Enhanced Neovim bridge with bidirectional communication"""

    def __init__(self, assistant, host="127.0.0.1", port=8001):
        self.assistant = assistant
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}
        self.running = False
        self._heartbeat_interval = 30  # Send ping every 30s
        self.message_handlers = {
            "chat": self._handle_chat_message,
            "complete": self._handle_completion,
            "explain": self._handle_explanation,
            "fix": self._handle_fix,
            "analyze": self._handle_analysis,
            "refactor": self._handle_refactor,
            "debug_analysis": self._handle_debug_analysis,
            "complete_as_you_type": self._handle_completion_as_you_type,
            "ping": lambda _: {"type": "pong"},  # Add ping handler
            "get_diagnostics": self._handle_get_diagnostics,  # Add get_diagnostics handler
            "verification_results": self._handle_verification_results,  # Add verification results handler
        }

    def _handle_get_diagnostics(self, payload):
        filepath = payload.get("filepath")
        if filepath:
            logger.info(f"Received get_diagnostics request for: {filepath}")
            try:
                # This is a placeholder for a real LSP client implementation
                # In a real scenario, you would use a library like `python-lsp-jsonrpc`
                # to communicate with the LSP server.
                diagnostics = self.assistant.get_diagnostics(filepath)
                return {
                    "type": "diagnostics_response",
                    "payload": {"diagnostics": diagnostics},
                }
            except Exception as e:
                logger.error(f"Error getting diagnostics: {e}")
                return {
                    "type": "error",
                    "payload": {"message": f"Error getting diagnostics: {e}"},
                }
        else:
            logger.warning("Received empty get_diagnostics payload.")
            return {
                "type": "error",
                "payload": {"message": "Empty get_diagnostics payload received"},
            }

    def _handle_chat_message(self, payload):
        message = payload.get("message")
        if message:
            logger.info(f"Received chat message from Neovim: {message}")
            # Delegate to the assistant to get a response
            response = self.assistant.get_response(
                message
            )  # Assuming get_response is synchronous or handles async internally
            # Send the response back to Neovim
            return {"type": "chat_response", "payload": {"response": response}}
        else:
            logger.warning("Received empty chat message payload.")
            return {
                "type": "error",
                "payload": {"message": "Empty chat message received"},
            }

    async def _handle_completion(self, payload):
        code = payload.get("code", "")
        try:
            suggestion = await self.assistant.process_query(
                f"Complete this code:\n{code}", payload.get("context", {})
            )
            return {"completion": suggestion}
        except Exception as e:
            logger.error(f"Error processing complete action: {e}")
            return {"error": f"Error processing complete action: {e}"}

    async def _handle_explanation(self, payload):
        code = payload.get("code", "")
        explanation = await self.assistant.process_query(
            f"Explain this code:\n{code}",
            payload.get("context", {}),
        )
        return {"explanation": explanation}

    async def _handle_fix(self, payload):
        code = payload.get("code", "")
        context = payload.get("context", {})
        fix_results = await self.assistant.process_fix_request(code, context)
        return {"fix_results": fix_results}

    async def _handle_analysis(self, payload):
        code = payload.get("code", "")
        analysis_results = await self.assistant.process_analysis_request(code)
        return {"analysis_results": analysis_results}

    async def _handle_refactor(self, payload):
        query = payload.get("query", "")
        refactor_results = await self.assistant.process_refactor_request(query)
        return {"refactor_results": refactor_results}

    async def _handle_debug_analysis(self, payload):
        query = payload.get("query", "")
        code = payload.get("code", "")
        debug_analysis_results = await self.assistant.process_debug_analysis_request(
            query, code
        )
        return {"debug_analysis_results": debug_analysis_results}

    async def _handle_completion_as_you_type(self, payload):
        code = payload.get("code", "")
        completion = await self.assistant.process_completion_request(
            code, payload.get("context", {})
        )
        return {"completion": completion}

    async def _handle_verification_results(self, payload):
        logger.info(f"Received verification results: {payload}")
        # You might want to pass these results to the assistant or log them more formally
        return {"status": "success", "message": "Verification results received."}

    def start(self):
        """Start bridge with heartbeat thread"""
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.server_socket.settimeout(1)

        # Start heartbeat thread
        threading.Thread(target=self._send_heartbeats, daemon=True).start()

        logger.info(f"Bridge started on {self.host}:{self.port}")

        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                self.clients[addr] = conn
                threading.Thread(
                    target=self._handle_client, args=(conn, addr), daemon=True
                ).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:  # Only log if not shutting down
                    logger.error(f"Accept error: {e}")

    def _send_heartbeats(self):
        """Periodically ping clients to prevent timeouts"""
        while self.running:
            time.sleep(self._heartbeat_interval)
            for addr, conn in list(self.clients.items()):
                try:
                    conn.sendall(json.dumps({"type": "ping"}).encode() + b"\n")
                except Exception as e:
                    logger.warning(f"Heartbeat failed for {addr}: {e}")
                    del self.clients[addr]

    def stop(self):
        """
        Stop the bridge server gracefully.
        """
        self.running = False
        if self.server_socket:
            self.server_socket.close()
            logger.info("Neovim bridge server socket closed.")

    def _handle_client(self, conn, addr):
        """Enhanced client handler with timeout detection"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        conn.settimeout(60)  # Drop idle clients after 60s
        try:
            with conn:
                logger.debug(f"Neovim client connected: {addr}")
                buffer = ""
                while self.running:
                    data = conn.recv(4096)
                    if not data:  # Client disconnected
                        break

                    buffer += data.decode("utf-8")

                    # Process all complete JSON objects in the buffer
                    while "\n" in buffer:
                        message_str, buffer = buffer.split("\n", 1)
                        if not message_str:
                            continue

                        try:
                            message = json.loads(message_str)
                            message_type = message.get("type") or message.get(
                                "action"
                            )  # Use 'type' or 'action'
                            payload = message.get(
                                "payload", message
                            )  # Use full message as payload if no 'payload' key

                            handler = self.message_handlers.get(message_type)
                            if handler:
                                if asyncio.iscoroutinefunction(handler):
                                    response = loop.run_until_complete(handler(payload))
                                else:
                                    response = handler(payload)
                                if response:
                                    conn.sendall(
                                        json.dumps(response).encode("utf-8") + b"\n"
                                    )
                            else:
                                logger.warning(
                                    f"No handler for message type: {message_type}. Full message: {message}"
                                )
                                conn.sendall(
                                    json.dumps(
                                        {
                                            "error": "No handler for message type",
                                            "type": message_type,
                                        }
                                    ).encode("utf-8")
                                    + b"\n"
                                )
                        except json.JSONDecodeError as e:
                            logger.error(
                                f"Error decoding JSON from client: {e} - Received: {message_str}"
                            )
                            conn.sendall(
                                json.dumps(
                                    {"error": "Invalid JSON", "details": str(e)}
                                ).encode("utf-8")
                                + b"\n"
                            )
                        except Exception as e:
                            logger.error(
                                f"Error processing message: {e}", exc_info=True
                            )
                            conn.sendall(
                                json.dumps(
                                    {
                                        "error": "Internal server error",
                                        "details": str(e),
                                    }
                                ).encode("utf-8")
                                + b"\n"
                            )
        except socket.timeout:
            logger.warning(f"Client {addr} timed out")
        except Exception as e:
            logger.error(f"Client {addr} error: {e}")
        finally:
            conn.close()
            self.clients.pop(addr, None)

    def send_to_client(self, message: dict):
        """Send a message to all connected Neovim clients."""
        for addr, conn in self.clients.items():
            try:
                conn.sendall(json.dumps(message).encode("utf-8"))
            except Exception as e:
                logger.error(f"Failed to send message to {addr}: {e}")
                # Remove the client if sending fails
                del self.clients[addr]

    def self_test(self) -> bool:
        """Performs a self-test of the NeovimBridge component.
        Returns True if the component is healthy, False otherwise.
        """
        logger.info("Running self-test for NeovimBridge...")
        import socket
        import threading
        import time

        # Mock Assistant for the test
        class MockAssistant:
            async def process_query(self, query: str, context: dict) -> str:
                await asyncio.sleep(0)  # Allow it to be awaited
                return f"Mock response to: {query}"

        test_host = "127.0.0.1"
        test_port = 5556  # Use a different port to avoid conflicts

        bridge = NeovimBridge(MockAssistant(), host=test_host, port=test_port)
        server_thread = threading.Thread(target=bridge.start, daemon=True)

        try:
            server_thread.start()
            time.sleep(0.5)  # Give server time to start

            # Test client connection
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.settimeout(5)
                client_socket.connect((test_host, test_port))
                logger.info("NeovimBridge self-test: Client connected.")

                # Send a test message
                test_message = {"action": "complete", "code": "print('hello')"}
                client_socket.sendall(json.dumps(test_message).encode("utf-8") + b"\n")
                response = client_socket.recv(4096).decode("utf-8").strip()

                if "Mock response" not in response:
                    logger.error(
                        f"NeovimBridge self-test failed: Unexpected response: {response}"
                    )
                    return False

            logger.info("NeovimBridge self-test passed.")
            return True
        except Exception as e:
            logger.error(f"NeovimBridge self-test failed: {e}")
            raise NeovimBridgeError(f"NeovimBridge self-test failed: {e}") from e
        finally:
            bridge.stop()
            server_thread.join(timeout=2)  # Give thread time to stop
            if server_thread.is_alive():
                logger.warning(
                    "NeovimBridge self-test: Server thread did not terminate gracefully."
                )

    def is_connected(self) -> bool:
        """Checks if there is at least one client connected."""
        return len(self.clients) > 0

    def is_listening(self) -> bool:
        """Checks if the server socket is actively listening for connections."""
        return self.server_socket is not None and self.running
