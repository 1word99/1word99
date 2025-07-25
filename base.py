"""
osmanli_ai/base.py - Core component system
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from osmanli_ai.core.enums import ComponentStatus
from osmanli_ai.core.types import ComponentMetadata

logger = logging.getLogger(__name__)


class BaseComponent(ABC):
    """
    Abstract base class for all system components.
    Implements core lifecycle management.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._status = ComponentStatus.CREATED
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @property
    def status(self) -> ComponentStatus:
        """Current runtime status."""
        return self._status

    @abstractmethod
    def get_metadata(self) -> ComponentMetadata:
        """Return component metadata."""

    def initialize(self) -> None:
        """Initialize component resources."""
        if self._status != ComponentStatus.CREATED:
            raise RuntimeError(f"Cannot initialize from {self._status} state")

        self._status = ComponentStatus.INITIALIZED
        self.logger.info(f"Initialized {self.get_metadata().name}")

    # ... keep all other BaseComponent methods unchanged ...
