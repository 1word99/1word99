"""
osmanli_ai/core/enums.py - Core enumerations
"""

from enum import Enum, auto


class ComponentType(Enum):
    """Core component type classification"""

    PLUGIN = auto()
    SERVICE = auto()
    MANAGER = auto()
    ADAPTER = auto()
    UTILITY = auto()
    AGENT = auto()


class ComponentStatus(Enum):
    """Runtime status of components"""

    CREATED = auto()
    INITIALIZED = auto()
    RUNNING = auto()
    PAUSED = auto()
    STOPPED = auto()
    ERROR = auto()
    WARNING = auto()


class PluginType(Enum):
    """Plugin type classification"""

    LLM = auto()
    KNOWLEDGE = auto()
    TOOL = auto()
    VISION = auto()
    MEDIA = auto()
    FINANCE = auto()
    CODE = auto()
    INTEGRATION = auto()


class SkillType(Enum):
    """Skill type classification"""

    COGNITIVE = auto()
    PHYSICAL = auto()
    SOCIAL = auto()
    CREATIVE = auto()


class EventType(Enum):
    """System event types"""

    MESSAGE_RECEIVED = auto()
    TASK_COMPLETED = auto()
    ERROR_OCCURRED = auto()
    STATE_CHANGED = auto()


class BrainState(Enum):
    """Brain operational states"""

    IDLE = auto()
    PROCESSING = auto()
    LEARNING = auto()
    SLEEPING = auto()
