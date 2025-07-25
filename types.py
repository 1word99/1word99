"""
osmanli_ai/core/types.py - Core type definitions
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TypedDict

# Corrected: Import enums from osmanli_ai.core.enums
from osmanli_ai.core.enums import ComponentType, EventType, PluginType, SkillType


@dataclass
class ComponentMetadata:
    """Standardized metadata for all components"""

    name: str
    version: str
    description: str
    component_type: ComponentType
    author: str = "Osmanli AI"
    config_schema: Optional[Dict[str, Any]] = None
    required_dependencies: Optional[List[str]] = None
    optional_dependencies: Optional[List[str]] = None
    # Fields that are specific to plugins but optional for other components
    plugin_type: Optional[PluginType] = None
    capabilities: Optional[List[str]] = None

    def __post_init__(self):
        self.required_dependencies = self.required_dependencies or []
        self.optional_dependencies = self.optional_dependencies or []
        if self.capabilities is not None:
            self.capabilities = self.capabilities or []
        else:
            self.capabilities = []


@dataclass
class PluginMetadata(ComponentMetadata):
    """Extended metadata for plugins"""

    ui_schema: Optional[Dict[str, Any]] = None  # Optional field (has default)

    def __post_init__(self):
        super().__post_init__()
        if self.plugin_type is None:
            raise TypeError("PluginMetadata requires a 'plugin_type'")
        if self.capabilities is None:
            self.capabilities = []


class SkillDefinition(TypedDict):
    """Structure for skill definitions"""

    name: str
    description: str
    skill_type: SkillType
    required_capabilities: List[str]


class EventPayload(TypedDict):
    """Standard event payload structure"""

    event_type: EventType
    source: str
    data: Dict[str, Any]
    timestamp: float
