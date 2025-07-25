from pathlib import Path
import subprocess
from typing import Any, Dict, Optional

from loguru import logger

from osmanli_ai.core.agent_manager import AgentManager
from osmanli_ai.core.code_analyzer import CodeAnalyzer

# CORRECTED IMPORT PATH for RequestDispatcher
from osmanli_ai.core.dispatcher import (
    RequestDispatcher,
)  # Changed from osmanli_ai.dispatcher
from osmanli_ai.core.events import EventManager
from osmanli_ai.core.exceptions import NeovimBridgeError
from osmanli_ai.core.memory import ConversationMemory  # Assuming this is in core
from osmanli_ai.core.quran_module import QuranKnowledgeBase  # Assuming this is in core
from osmanli_ai.core.skills import SkillManager
from osmanli_ai.core.stock_monitor import StockMonitor
from osmanli_ai.core.component_status import ComponentStatus
from osmanli_ai.core.user_profile import UserProfile
from osmanli_ai.utils.interprocess.neovim_bridge_client import NeovimBridgeClient
from osmanli_ai.utils.plugin_manager_util import PluginManager
from osmanli_ai.utils.project_explorer import ProjectExplorer
from osmanli_ai.core.osmanli_ai_fixer import AICodeFixer
from osmanli_ai.core.living_fixer import LivingCodeFixer
from osmanli_ai.core.osmanli_ai_project_analyzer import ProjectAnalyzer
from osmanli_ai.core.terminal_integration import TerminalIntegration
from osmanli_ai.core.package_manager import PackageManager
import tempfile
import os


class Assistant:
    """Modern assistant with integrated financial capabilities"""

    def __init__(
        self,
        config: Dict[str, Any],
        plugin_manager: PluginManager,
        quran_knowledge_base: Optional[QuranKnowledgeBase] = None,
        brain: Optional[Any] = None,
        user_profile: Optional[UserProfile] = None,
        agent_manager: Optional[AgentManager] = None,
        project_root: Path = Path("."),  # Add project_root parameter
    ):
        logger.info("Assistant: Initializing...")
        self.config = config
        self.plugins = plugin_manager
        self.quran = quran_knowledge_base
        self.brain = brain  # Store the brain instance
        memory_config = self.config.get("memory", {})
        max_history_length = memory_config.get("max_history_length", 50)
        self.memory = ConversationMemory(max_history_length)
        self.user_profile = user_profile or UserProfile(
            "default_user", Path("./user_profiles")
        )
        self.agent_manager = agent_manager or AgentManager(
            self.config.get("agent_manager", {})
        )
        self.event_manager = EventManager()
        self.skill_manager = SkillManager()
        self.code_analyzer = CodeAnalyzer()
        self.project_explorer = ProjectExplorer(
            Path(".")
        )  # Initialize with current directory
        self.stock_monitor = StockMonitor(self.config.get("stock_monitor", {}))
        self.dispatcher = RequestDispatcher(self)
        self.pending_action = None
        self.project_root = project_root  # Store project_root
        self.active_agent: str = "default"  # Initialize active agent to default

        # Initialize fixers
        self.ai_code_fixer = AICodeFixer(self.project_root)
        self.living_fixer = LivingCodeFixer(
            self.project_root, brain=self.brain
        )  # Pass brain to LivingCodeFixer
        self.project_analyzer = ProjectAnalyzer(self.project_root)
        self.terminal_integration = TerminalIntegration()
        self.package_manager = PackageManager()

        try:
            neovim_config = (
                self.config.get("system", {}).get("interfaces", {}).get("neovim", {})
            )
            neovim_host = neovim_config.get("host", "localhost")
            neovim_port = neovim_config.get("port", 8001)
            self.neovim_bridge_client = NeovimBridgeClient(
                host=neovim_host, port=neovim_port
            )
            logger.info("Assistant: Neovim bridge client initialized.")
        except NeovimBridgeError as e:
            logger.warning(
                f"Assistant: Neovim bridge client could not be initialized: {e}"
            )
            self.neovim_bridge_client = None

    async def connect_neovim_bridge(self):
        """Connects the Neovim bridge client asynchronously."""
        if self.neovim_bridge_client:
            logger.info("Assistant: Attempting to connect Neovim bridge client...")
            try:
                connection_successful = await self.neovim_bridge_client.connect()
                if connection_successful:
                    logger.info(
                        "Assistant: Neovim bridge client connected successfully."
                    )
                else:
                    logger.warning(
                        "Assistant: Neovim bridge client connection failed (connect() returned False)."
                    )
            except Exception as e:
                logger.error(f"Assistant: Failed to connect Neovim bridge client: {e}")
        else:
            logger.warning(
                "Assistant: Neovim bridge client not initialized, skipping connection attempt."
            )

        logger.info("Assistant: Initialization complete.")

    async def process_query(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        logger.debug(
            f"Assistant: Processing query: '{query}' with active agent: {self.active_agent}"
        )
        self.memory.add_message("user", query)

        # Analyze the context of the query
        _ = self.brain.context_manager.analyze(query)

        # Route the query based on the context
        if context.get("needs_terminal"):
            response = self.handle_terminal_command(query)
        elif context.get("needs_package_management"):
            # This is a simplified example; you'll want to parse the query to determine the specific command
            response = self.install_dependencies(self.project_root)
        elif context.get("needs_code_action"):
            # This is a simplified example; you'll want to get the current file content
            response = self.brain.code_actions.suggest_refactoring("")
        else:
            response = await self.dispatcher.route(query=query, context=context)

        self.memory.add_message("assistant", response)
        logger.debug(
            f"Assistant: Query processing complete. Response: {response[:100]}..."
        )
        return response

    def get_stock_price(self, symbol: str) -> str:
        """
        Retrieves the stock price using the StockMonitor plugin.
        """
        if self.stock_monitor:
            if self.stock_monitor.status != ComponentStatus.INITIALIZED:
                self.stock_monitor.initialize()  # Ensure it's initialized before use
            if self.stock_monitor.status == ComponentStatus.INITIALIZED:
                return self.stock_monitor.process(f"price of {symbol}")
            else:
                return f"StockMonitor not ready. Status: {self.stock_monitor.status}. Check API key."
        return "Stock plugin is not available to handle financial queries."

    def conduct_project_review(self, project_path: Path) -> str:
        """Conducts a review of the specified project path."""
        logger.info(f"Conducting project review for: {project_path}")
        # Placeholder for actual project review logic
        return f"Project review for {project_path} initiated. (Placeholder)"

    async def process_fix_request(
        self, code: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        logger.info("Processing fix request from Neovim.")
        # Create a temporary file to write the code to
        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".py"
        ) as tmp_file:
            tmp_file.write(code)
            tmp_file_path = Path(tmp_file.name)

        try:
            # Call the AICodeFixer to fix the code
            # Note: AICodeFixer.fix_project operates on the whole project.
            # For single file fixes, we might need a more granular method in AICodeFixer
            # For now, we'll simulate a fix on the temp file.
            # In a real scenario, AICodeFixer would need to be adapted to fix a specific file.
            # For demonstration, we'll just return a success message.
            # self.ai_code_fixer.fix_project() # This would run on the whole project

            # Simulate a fix for the given code
            fixed_code = code.replace(
                "old_bug", "new_fix"
            )  # Placeholder for actual fix logic

            # Overwrite the temporary file with fixed code for demonstration
            with open(tmp_file_path, "w") as f:
                f.write(fixed_code)

            return {
                "status": "success",
                "message": "Code fix simulated successfully.",
                "fixed_code": fixed_code,
            }
        except Exception as e:
            logger.error(f"Error processing fix request: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            os.remove(tmp_file_path)  # Clean up the temporary file

    async def process_analysis_request(self, code: str) -> Dict[str, Any]:
        logger.info("Processing analysis request from Neovim.")
        # Create a temporary file to write the code to
        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".py"
        ) as tmp_file:
            tmp_file.write(code)
            tmp_file_path = Path(tmp_file.name)

        try:
            # Call the AICodeFixer for syntax analysis
            # AICodeFixer.fix_syntax_errors actually checks for syntax errors and returns False if none found
            # We need a method that returns diagnostics/analysis results.
            # For now, we'll simulate analysis results.

            # Simulate analysis results
            analysis_results = {
                "issues": [
                    {
                        "line": 1,
                        "column": 1,
                        "message": "Missing docstring",
                        "severity": "info",
                    },
                    {
                        "line": 5,
                        "column": 10,
                        "message": "Variable 'x' might be undefined",
                        "severity": "warning",
                    },
                ]
            }
            return {
                "status": "success",
                "message": "Code analysis simulated successfully.",
                "analysis_results": analysis_results,
            }
        except Exception as e:
            logger.error(f"Error processing analysis request: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            os.remove(tmp_file_path)  # Clean up the temporary file

    async def process_refactor_request(self, query: str) -> Dict[str, Any]:
        logger.info(f"Processing refactor request: {query}")
        try:
            # Get relevant project context
            _ = self.project_analyzer.get_relevant_context(query)

            # In a real scenario, you would send this query and context to your LLM
            # for refactoring suggestions and proposed changes.
            # For now, we'll simulate a refactoring operation.

            simulated_changes = [
                {
                    "filepath": "main.py",
                    "action": "replace",
                    "old_string": "import os",
                    "new_string": "import os\nimport sys",
                },
                {
                    "filepath": "osmanli_ai/core/assistant.py",
                    "action": "write",
                    "content": "# This is a simulated new file content\nprint('Hello from new file')",
                },
            ]

            # Apply the simulated changes
            results = self.project_analyzer.apply_changes(simulated_changes)

            return {
                "status": "success",
                "message": "Refactoring simulated and applied.",
                "changes_applied": results,
            }
        except Exception as e:
            logger.error(f"Error processing refactor request: {e}")
            return {"status": "error", "message": str(e)}

    async def process_debug_analysis_request(
        self, query: str, code: str
    ) -> Dict[str, Any]:
        logger.info(f"Processing debug analysis request: {query}")
        logger.debug(f"Code: {code}")

        # In a real scenario, you would send this to your LLM for analysis.
        # For now, we'll simulate a response.

        simulated_analysis = f'Based on your query "{query}" and the provided code snippet, it appears the issue might be related to an unhandled edge case in the loop condition. Consider adding a check for empty input.'

        return {"status": "success", "analysis": simulated_analysis}

    async def initiate_auto_repair_workflow(self):
        logger.info("Initiating auto-repair workflow...")
        # 1. Project File Discovery
        all_py_files = list(self.project_root.rglob("*.py"))
        logger.info(f"Found {len(all_py_files)} Python files to analyze.")

        for filepath in all_py_files:
            relative_filepath = filepath.relative_to(self.project_root)
            logger.info(f"Processing file: {relative_filepath}")
            try:
                await self.living_fixer.conscious_fix(filepath)
            except Exception as e:
                logger.error(f"Error processing {relative_filepath}: {e}")

        logger.info("Running post-repair verification checks...")
        verification_results = {"tests": "", "linting": ""}

        # Run pytest
        try:
            pytest_result = subprocess.run(["pytest"], capture_output=True, text=True)
            verification_results["tests"] = pytest_result.stdout + pytest_result.stderr
            logger.info("Pytest execution completed.")
        except Exception as e:
            verification_results["tests"] = f"Pytest execution failed: {e}"
            logger.error(f"Pytest execution failed: {e}")

        # Run ruff check
        try:
            ruff_result = subprocess.run(
                ["ruff", "check", "."], capture_output=True, text=True
            )
            verification_results["linting"] = ruff_result.stdout + ruff_result.stderr
            logger.info("Ruff execution completed.")
        except Exception as e:
            verification_results["linting"] = f"Ruff execution failed: {e}"
            logger.error(f"Ruff execution failed: {e}")

        if self.neovim_bridge_client and self.neovim_bridge_client.is_connected():
            await self.neovim_bridge_client.send_notification(
                {"action": "verification_results", "results": verification_results}
            )
            logger.info("Sent verification results to Neovim.")
        else:
            logger.warning(
                "Neovim bridge not connected. Cannot send verification results."
            )

    def get_diagnostics(self, filepath: str) -> list:
        """Gets diagnostics for a given file path."""
        # In a real implementation, this would communicate with a language server
        # to get diagnostics for the given file.
        logger.info(f"Getting diagnostics for {filepath}...")
        return []

    async def process_completion_request(
        self, code: str, context: Dict[str, Any]
    ) -> str:
        logger.info("Processing completion request from Neovim.")
        # In a real scenario, you would send this code to your LLM
        # and get a completion. For now, we'll simulate it.

        # Simulate a simple completion
        if code.endswith("imp"):
            return "import os"
        elif code.endswith("def f"):
            return "def my_function():\n    pass"
        else:
            return ""

    def self_test(self) -> bool:
        """Performs a self-test of the Assistant component.
        Returns True if the component is healthy, False otherwise.
        """
        logger.info("Running self-test for Assistant...")
        if not self.config:
            logger.error("Assistant self-test failed: Config not loaded.")
            return False
        if not self.plugins:
            logger.error("Assistant self-test failed: Plugin manager not loaded.")
            return False
        if not self.memory:
            logger.error("Assistant self-test failed: Memory not initialized.")
            return False
        if not self.user_profile:
            logger.error("Assistant self-test failed: User profile not initialized.")
            return False
        if not self.agent_manager:
            logger.error("Assistant self-test failed: Agent manager not initialized.")
            return False
        logger.info("Assistant self-test passed.")
        return True

    def get_response(self, query: str) -> str:
        """Synchronous wrapper for process_query for use with Tkinter"""
        if query.lower().strip() == "neovim":
            try:
                subprocess.Popen(["gnome-terminal", "--", "nvim"])
                return "Neovim launched in a new terminal."
            except FileNotFoundError:
                return "Error: Could not launch Neovim. Please ensure 'gnome-terminal' and 'nvim' are installed."
            except Exception as e:
                return f"An error occurred: {e}"

        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # 'RuntimeError: There is no current event loop...'
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        response = loop.run_until_complete(self.process_query(query))

        # Check for code blocks and send to Neovim
        if "```" in response:
            code_blocks = response.split("```")
            for i, block in enumerate(code_blocks):
                if i % 2 == 1:  # Code is in the odd-indexed blocks
                    # The language is on the first line, so we skip it
                    code = "\n".join(block.split("\n")[1:])
                    if self.neovim_bridge:
                        try:
                            self.neovim_bridge.send_notification(
                                {"action": "code_generation", "code": code}
                            )
                            return "I've sent the code to Neovim."
                        except Exception as e:
                            return f"An error occurred: {e}"
                    else:
                        return "Neovim bridge is not available."

        return response

    def handle_terminal_command(self, command: str) -> str:
        """Executes a terminal command and returns the output."""
        stdout, stderr = self.terminal_integration.execute(command)
        if stderr:
            return f"Error: {stderr}"
        return stdout

    def install_dependencies(self, project_path: str) -> str:
        """Installs dependencies for a project."""
        success = self.package_manager.install_dependencies(project_path)
        if success:
            return "Dependencies installed successfully."
        return "Failed to install dependencies."

    def check_vulnerabilities(self, project_path: str) -> str:
        """Checks for vulnerabilities in project dependencies."""
        vulnerabilities = self.package_manager.check_vulnerabilities(project_path)
        if vulnerabilities:
            return f"Found vulnerabilities: {vulnerabilities}"
        return "No vulnerabilities found."
