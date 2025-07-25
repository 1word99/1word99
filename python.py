# osmanli_ai/core/language_server/plugins/python.py

from .plugin import LanguageServerPlugin


class PythonLanguageServerPlugin(LanguageServerPlugin):
    """
    A language server plugin for Python.
    """

    def get_completions(self, file_path, position):
        """
        Gets code completions for a given file and position.
        (This is a placeholder for a real implementation)
        """
        return ["def", "class", "import"]

    def get_diagnostics(self, file_path):
        """
        Gets diagnostics (errors, warnings) for a file.
        (This is a placeholder for a real implementation)
        """
        return [
            {
                "range": {
                    "start": {"line": 0, "character": 0},
                    "end": {"line": 0, "character": 5},
                },
                "message": "This is a sample diagnostic.",
                "severity": 1,  # 1 for error, 2 for warning
            }
        ]
