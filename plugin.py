# osmanli_ai/core/language_server/plugins/plugin.py

from abc import ABC, abstractmethod


class LanguageServerPlugin(ABC):
    """
    Abstract base class for all language server plugins.
    """

    @abstractmethod
    def get_completions(self, file_path, position):
        """
        Gets code completions for a given file and position.
        """
        pass

    @abstractmethod
    def get_diagnostics(self, file_path):
        """
        Gets diagnostics (errors, warnings) for a file.
        """
        pass
