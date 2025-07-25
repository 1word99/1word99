import logging
import psutil

logger = logging.getLogger(__name__)


class ContextAwareness:
    """
    Gathers information about the system's state.
    """

    def get_context(self, component_name: str) -> dict:
        """
        Gathers context for a specific component.
        """
        logger.info(f"Gathering context for {component_name}.")
        # Placeholder logic
        return {}

    def get_system_context(self) -> dict:
        """
        Gathers system-wide context.
        """
        logger.info("Gathering system context.")
        return {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
        }
