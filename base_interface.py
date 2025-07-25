"""
Provides a common base class for AI assistant interfaces.
"""

import logging

logger = logging.getLogger(__name__)


class BaseInterface:
    """
    Base class providing common initialization logic for AI assistant interfaces.
    """

    def __init__(self, assistant, memory, config):
        self.assistant = assistant
        self.memory = memory
        self.config = config
        logger.info("BaseInterface initialized with common components.")
