import importlib
import inspect
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from osmanli_ai.base import BaseComponent
from osmanli_ai.core.agent import BaseAgent
from osmanli_ai.core.enums import ComponentType
from osmanli_ai.core.exceptions import AgentError
from osmanli_ai.core.types import ComponentMetadata


class AgentManager(BaseComponent):
    """
    Manages the discovery, loading, and lifecycle of autonomous agents.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_dirs = [
            Path(d) for d in config.get("agent_dirs", ["osmanli_ai/agents"])
        ]
        self.component_type = ComponentType.MANAGER
        logger.info("AgentManager initialized.")

    def get_metadata(self) -> ComponentMetadata:
        return ComponentMetadata(
            name="AgentManager",
            version="1.0.0",
            author="Osmanli AI",
            description="Manages the discovery, loading, and lifecycle of autonomous agents.",
            component_type=ComponentType.MANAGER,
        )

    async def load_agents(self) -> None:
        """
        Discovers and loads agent implementations from specified directories.
        """
        for agent_dir in self.agent_dirs:
            if not agent_dir.exists():
                logger.warning(f"Agent directory missing: {agent_dir}")
                continue

            logger.debug(f"Scanning for agents in: {agent_dir}")
            for agent_file in agent_dir.glob("**/*.py"):
                if (
                    agent_file.name.startswith(("_", "."))
                    or agent_file.name == "__init__.py"
                ):
                    logger.debug(
                        f"Skipping hidden, special, or __init__.py file: {agent_file.name}"
                    )
                    continue

                try:
                    agent_instance = self._load_single_agent(agent_file)
                    if agent_instance:
                        self._initialize_and_register(agent_instance)
                    else:
                        logger.warning(
                            f"No valid agent class found in {agent_file.name}"
                        )
                except Exception as e:
                    logger.error(
                        f"Agent loading failed for {agent_file.name}: {e}",
                        exc_info=True,
                    )
                    raise AgentError(
                        f"Agent loading failed for {agent_file.name}: {e}"
                    ) from e

    def _load_single_agent(self, agent_file: Path) -> Optional[BaseAgent]:
        """
        Loads a single agent from a Python file.
        """
        module_name = f"osmanli_ai.agents.{agent_file.stem}"  # Assuming agents are in osmanli_ai/agents
        spec = importlib.util.spec_from_file_location(module_name, agent_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for name, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, BaseAgent) and cls is not BaseAgent:
                return cls(self.config)  # Instantiate the agent
        return None

    def _initialize_and_register(self, agent_instance: BaseAgent) -> None:
        """
        Initializes and registers an agent.
        """
        try:
            agent_instance.initialize()
            agent_name = agent_instance.get_metadata().name
            self.agents[agent_name] = agent_instance
            logger.info(f"Loaded and initialized agent: {agent_name}")
        except Exception as e:
            logger.error(
                f"Failed to initialize agent {agent_instance.get_metadata().name}: {e}",
                exc_info=True,
            )
            raise AgentError(
                f"Failed to initialize agent {agent_instance.get_metadata().name}: {e}"
            ) from e

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        Retrieves a loaded agent by its name.
        """
        return self.agents.get(name)

    def get_all_agents(self) -> Dict[str, BaseAgent]:
        """
        Returns all loaded agents.
        """
        return self.agents

    async def shutdown(self) -> None:
        """
        Shuts down all loaded agents.
        """
        for agent_name, agent in self.agents.items():
            try:
                await agent.shutdown()
                logger.info(f"Agent {agent_name} shut down.")
            except Exception as e:
                logger.error(
                    f"Error shutting down agent {agent_name}: {e}", exc_info=True
                )
                raise AgentError(f"Error shutting down agent {agent_name}: {e}") from e

    def self_test(self) -> bool:
        """
        Performs a self-test of the AgentManager component.
        """
        logger.info("Running self-test for AgentManager...")
        # This self-test is basic; a more comprehensive one would involve loading dummy agents
        try:
            # Create a temporary directory for test agents
            import shutil
            import tempfile

            test_agent_dir = Path(tempfile.mkdtemp())
            # Create a dummy agent file
            dummy_agent_content = """
from osmanli_ai.core.agent import BaseAgent
from osmanli_ai.core.types import ComponentMetadata
from osmanli_ai.core.enums import ComponentType

class DummyAgent(BaseAgent):
    def __init__(self, config):
        super().__init__(config)
    @classmethod
    def get_metadata(cls) -> ComponentMetadata:
        return ComponentMetadata(
            name="DummyAgent",
            version="1.0.0",
            author="Test",
            description="A dummy agent for testing.",
            component_type=ComponentType.AGENT,
        )
    async def process_task(self, task, context=None):
        return {"status": "success", "result": "Dummy task processed."}
    def can_handle_query(self, query: str) -> bool:
        return "dummy" in query
"""
            (test_agent_dir / "dummy_agent.py").write_text(dummy_agent_content)

            # Temporarily change agent_dirs to the test directory
            original_agent_dirs = self.agent_dirs
            self.agent_dirs = [test_agent_dir]

            # Test loading the dummy agent
            self.agents.clear()  # Clear existing agents for a clean test
            import asyncio

            asyncio.run(self.load_agents())

            if "DummyAgent" not in self.agents:
                logger.error("AgentManager self-test failed: Dummy agent not loaded.")
                return False

            # Test getting the agent
            dummy_agent = self.get_agent("DummyAgent")
            if not dummy_agent:
                logger.error(
                    "AgentManager self-test failed: Could not retrieve dummy agent."
                )
                return False

            # Test processing a task
            result = asyncio.run(dummy_agent.process_task({"type": "test"}))
            if result["status"] != "success":
                logger.error(
                    "AgentManager self-test failed: Dummy agent task processing failed."
                )
                return False

            logger.info("AgentManager self-test passed.")
            return True
        except Exception as e:
            logger.error(f"AgentManager self-test failed: {e}", exc_info=True)
            raise AgentError(f"AgentManager self-test failed: {e}") from e
        finally:
            # Restore original agent_dirs and clean up temporary directory
            if test_agent_dir and test_agent_dir.exists():
                shutil.rmtree(test_agent_dir)
            self.agent_dirs = original_agent_dirs
