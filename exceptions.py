class OsmanliAIException(Exception):
    """Base exception for Osmanli AI application errors."""


class ConfigurationError(OsmanliAIException):
    """Raised when there is an issue with the application configuration."""


class PluginError(OsmanliAIException):
    """Raised when there is an issue with a plugin (loading, processing, etc.)."""


class AgentError(OsmanliAIException):
    """Raised when there is an issue with an agent (loading, processing, etc.)."""


class VoiceProcessingError(OsmanliAIException):
    """Raised when there is an issue during speech-to-text or text-to-speech processing."""


class NeovimBridgeError(OsmanliAIException):
    """Raised when there is an issue with the Neovim bridge communication."""


class UserProfileError(OsmanliAIException):
    """Raised when there is an issue with user profile operations."""


class QuranKnowledgeBaseError(OsmanliAIException):
    """Raised when there is an issue with the Quran knowledge base operations."""
