from enum import Enum, auto
from typing import Dict, Any

class ComponentType(Enum):
    """Defines the types of components in the Osmanli AI system."""
    CORE = auto()
    AGENT = auto()
    PLUGIN = auto()
    INTERFACE = auto()
    UTILITY = auto()
    STORAGE = auto()
    SENSOR = auto()
    VISUALIZATION = auto()
    SECURITY = auto()
    DEBUGGING = auto()
    META = auto()  # For meta-level components like Orchestrator, AICortex
    ORCHESTRATOR = auto()
    AICORTEX = auto()
    ANALYSIS_WORKER = auto()
    FIX_SUGGESTION_WORKER = auto()
    REPAIR_WORKER = auto()

class Status(Enum):
    """Defines the operational status of a component."""
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    IDLE = "idle" # Added IDLE for workers

class ComponentStatusManager:
    """
    Manages and tracks the operational status of various components in the system.
    """
    def __init__(self):
        self._statuses: Dict[ComponentType, Dict[str, str]] = {}

    def update_status(self, component_type: ComponentType, status: Status, message: str = ""):
        """Updates the status of a specific component."""
        self._statuses[component_type] = {"status": status.value, "message": message}

    def get_status(self, component_type: ComponentType) -> Dict[str, str]:
        """Returns the status of a specific component."""
        return self._statuses.get(component_type, {"status": Status.STOPPED.value, "message": "Not reported"})

    def get_all_statuses(self) -> Dict[str, Dict[str, str]]:
        """Returns the statuses of all tracked components."""
        return {comp_type.name: status_info for comp_type, status_info in self._statuses.items()}
