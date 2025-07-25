from abc import abstractmethod
from typing import Any, Dict, Optional

from loguru import logger

from osmanli_ai.base import BaseComponent
from osmanli_ai.core.enums import ComponentType
from osmanli_ai.core.exceptions import AgentError
from osmanli_ai.core.types import ComponentMetadata


class BaseAgent(BaseComponent):
    """
    Abstract base class for all autonomous agents in the Osmanli AI system.
    Agents are specialized components capable of processing tasks and potentially
    collaborating with other agents.
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.component_type = ComponentType.AGENT
        logger.info(f"Agent {self.get_metadata().name} initialized.")

    @abstractmethod
    async def process_task(
        self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processes a given task. This is the primary method for an agent's operation.

        Args:
            task (Dict[str, Any]): A dictionary representing the task to be processed.
                                   Expected to contain at least a 'type' and 'payload'.
            context (Optional[Dict[str, Any]]): Additional context for the task.

        Returns:
            Dict[str, Any]: A dictionary containing the result of the task processing.
        """

    def can_handle_query(self, query: str) -> bool:
        """
        Determines if the agent can handle a given natural language query.
        Agents should override this method with their specific intent recognition logic.

        Args:
            query (str): The natural language query from the user.

        Returns:
            bool: True if the agent can handle the query, False otherwise.
        """
        return False  # Default: agent cannot handle any query unless overridden

    @classmethod
    def get_metadata(cls) -> ComponentMetadata:
        """
        Returns the metadata for the agent.
        Agents should override this to provide specific details.
        """
        return ComponentMetadata(
            name=cls.__name__,
            version="0.1.0",
            description="A generic base agent.",
            component_type=ComponentType.AGENT,
            author="Osmanli AI",
        )

    async def shutdown(self):
        """
        Cleanup resources before shutdown.
        Override in child classes if needed.
        """
        logger.info(f"Shutting down {self.get_metadata().name} agent.")

    def self_test(self) -> bool:
        """
        Performs a self-test of the agent component.
        Agents should override this to provide specific test logic.
        """
        logger.info(f"Running self-test for {self.get_metadata().name}...")
        # Basic test: ensure metadata is available
        try:
            metadata = self.get_metadata()
            if not metadata.name or not metadata.version:
                logger.error(
                    f"Agent {metadata.name} self-test failed: Missing metadata."
                )
                return False
            logger.info(f"Agent {metadata.name} self-test passed.")
            return True
        except Exception as e:
            logger.error(f"Agent self-test failed: {e}", exc_info=True)
            raise AgentError(f"Agent self-test failed: {e}") from e
