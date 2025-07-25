"""
Specialized base for utilities
"""

from osmanli_ai.base import BaseComponent, ComponentMetadata

# Corrected: Import ComponentType directly from osmanli_ai.core.enums
from osmanli_ai.core.enums import ComponentType


class BaseUtility(BaseComponent):
    """Extended base for all utilities"""

    @classmethod
    def get_metadata(cls) -> ComponentMetadata:
        """Utility-specific metadata"""
        meta = super().get_metadata()
        meta.component_type = ComponentType.UTILITY
        return meta

    # Add utility-specific methods here
    def validate_config(self):
        """Extended config validation"""
        pass  # Placeholder for actual validation logic
