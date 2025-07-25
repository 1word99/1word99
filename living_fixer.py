# osmanli_ai/core/living_fixer.py

import logging
import json
import ast
import asyncio
from pathlib import Path
from typing import Optional, Any, Dict

from .osmanli_ai_fixer import AICodeFixer
from osmanli_ai.utils.interprocess.neovim_bridge_client import NeovimBridgeClient
from osmanli_ai.core.configuration_manager import Config
from osmanli_ai.core.code_actions import CodeActions


logger = logging.getLogger(__name__)


class LivingCodeFixer(AICodeFixer):
    """Adds conscious repair capabilities while preserving original functionality"""

    def __init__(
        self,
        project_root: Path,
        config_path: str = "config.json",
        neovim_bridge_client: Optional[NeovimBridgeClient] = None,
        brain: Optional[Any] = None,
    ):
        super().__init__(project_root)
        self.mind_connected = False
        self.neovim_client = neovim_bridge_client
        self.current_buffer_content: str = ""
        self.current_cursor_position: Dict[str, int] = {"row": 0, "col": 0}
        self.config = Config(config_path)
        self.ast_tree: Optional[ast.Module] = None
        self.brain = brain
        self.code_actions = CodeActions()

    async def connect_mind(self):
        """Link to Neovim's consciousness asynchronously"""
        if not self.neovim_client:
            logger.warning(
                "Couldn't connect to Neovim mind: NeovimBridgeClient not provided."
            )
            return

        max_retries = 30
        retry_delay = 0.5
        for i in range(max_retries):
            if self.neovim_client.is_connected():
                self.mind_connected = True
                logger.info("Successfully connected to Neovim mind via bridge.")
                # Register to handle messages from Neovim
                self.neovim_client.register_message_handler(self._handle_neovim_message)
                return
            logger.info(
                f"Attempt {i+1}/{max_retries}: NeovimBridgeClient not yet connected. Retrying in {retry_delay}s..."
            )
            await asyncio.sleep(retry_delay)

        logger.warning(
            "Couldn't connect to Neovim mind: NeovimBridgeClient not connected after multiple retries."
        )

    async def send_to_neovim(self, message_type: str, payload: Dict[str, Any]):
        """Sends a structured message to Neovim via the bridge client."""
        if not self.mind_connected or not self.neovim_client:
            logger.warning("Not connected to Neovim mind. Cannot send message.")
            return
        try:
            full_message = {"type": message_type, "payload": payload}
            # Assuming the client has a method like `send_notification` or `send_message`
            await self.neovim_client.send_message(json.dumps(full_message))
            logger.info(f"Sent message of type '{message_type}' to Neovim.")
        except Exception as e:
            logger.error(f"Failed to send message to Neovim: {e}")

    async def conscious_fix(self, filepath: Path) -> bool:
        """Use Neovim's 'mind' for contextual repairs and send fix proposals."""
        if not self.mind_connected:
            logger.info(f"Not connected to Neovim, falling back for {filepath}")
            return False

        if not self.brain:
            logger.warning(
                "LivingCodeFixer not connected to AICortex. Cannot perform conscious fix."
            )
            return False

        try:
            content = filepath.read_text(encoding="utf-8")
            self.current_buffer_content = content

            # Use the brain's problem detector to find issues
            file_analyses = {
                str(filepath): self.brain.code_analyzer.analyze_python_file(content)
            }
            detected_problems = self.brain.problem_detector.detect_problems(
                self.project_root, file_analyses
            )

            if detected_problems:
                logger.info(
                    f"Detected {len(detected_problems)} problems in {filepath}. Attempting to fix..."
                )
                # Queue problems for the brain's repair worker
                self.brain.repair_worker_queue.put(detected_problems)

                # Send proposals to Neovim (simplified for now)
                proposals_for_neovim = []
                for problem in detected_problems:
                    proposals_for_neovim.append(
                        {
                            "filepath": str(filepath),
                            "line": problem.get("line", 1),
                            "description": problem.get("description", ""),
                            "fix_type": problem.get("type", ""),
                        }
                    )
                await self.send_to_neovim(
                    "fix_proposals",
                    {"filepath": str(filepath), "proposals": proposals_for_neovim},
                )
                logger.info(
                    f"Sent {len(proposals_for_neovim)} fix proposals to Neovim for {filepath}."
                )
                return True
            else:
                logger.info(f"No problems detected in {filepath} by AICortex.")
                return False

        except Exception as e:
            logger.error(f"Conscious fix failed for {filepath}: {e}", exc_info=True)
            return False
