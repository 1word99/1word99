# osmanli_ai/core/osmanli_ai_project_analyzer.py

from pathlib import Path
from typing import Dict, List, Any


class ProjectAnalyzer:
    def __init__(self, project_root: Path):
        self.project_root = project_root

    def get_project_structure(self) -> Dict[str, Any]:
        """Recursively gets the project structure (files and directories)."""
        structure = {"name": self.project_root.name, "type": "dir", "children": []}
        for item in self.project_root.iterdir():
            if item.is_dir():
                structure["children"].append(self._get_dir_structure(item))
            elif item.is_file():
                structure["children"].append({"name": item.name, "type": "file"})
        return structure

    def _get_dir_structure(self, path: Path) -> Dict[str, Any]:
        dir_structure = {"name": path.name, "type": "dir", "children": []}
        try:
            for item in path.iterdir():
                if item.is_dir():
                    dir_structure["children"].append(self._get_dir_structure(item))
                elif item.is_file():
                    dir_structure["children"].append(
                        {"name": item.name, "type": "file"}
                    )
        except PermissionError:
            dir_structure["children"].append(
                {"name": "(Permission Denied)", "type": "info"}
            )
        return dir_structure

    def get_file_content(self, relative_path: str) -> str | None:
        """Gets the content of a specific file within the project."""
        file_path = self.project_root / relative_path
        if file_path.is_file():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                return f"Error reading file: {e}"
        return None

    def get_relevant_context(self, query: str) -> Dict[str, Any]:
        """Simulates getting relevant project context based on a query.
        In a real scenario, this would involve semantic search, AST analysis, etc.
        """
        context = {
            "project_structure": self.get_project_structure(),
            "relevant_files": {},
        }

        # Simple keyword-based simulation for demonstration
        if "main.py" in query.lower():
            content = self.get_file_content("main.py")
            if content:
                context["relevant_files"]["main.py"] = content
        if "assistant.py" in query.lower():
            content = self.get_file_content("osmanli_ai/core/assistant.py")
            if content:
                context["relevant_files"]["osmanli_ai/core/assistant.py"] = content

        return context

    def apply_changes(self, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Applies a list of changes to files in the project.
        Each change dict should have 'filepath', 'action' (e.g., 'write', 'replace'), and 'content' or 'old_string'/'new_string'.
        """
        results = {"status": "success", "applied_changes": []}
        for change in changes:
            filepath = self.project_root / change["filepath"]
            action = change["action"]

            try:
                if action == "write":
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(change["content"])
                    results["applied_changes"].append(
                        {
                            "filepath": change["filepath"],
                            "action": "write",
                            "status": "success",
                        }
                    )
                elif action == "replace":
                    current_content = self.get_file_content(change["filepath"])
                    if current_content:
                        new_content = current_content.replace(
                            change["old_string"], change["new_string"]
                        )
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        results["applied_changes"].append(
                            {
                                "filepath": change["filepath"],
                                "action": "replace",
                                "status": "success",
                            }
                        )
                    else:
                        results["applied_changes"].append(
                            {
                                "filepath": change["filepath"],
                                "action": "replace",
                                "status": "failed",
                                "reason": "File not found or readable",
                            }
                        )
                else:
                    results["applied_changes"].append(
                        {
                            "filepath": change["filepath"],
                            "action": action,
                            "status": "failed",
                            "reason": "Unknown action",
                        }
                    )
            except Exception as e:
                results["applied_changes"].append(
                    {
                        "filepath": change["filepath"],
                        "action": action,
                        "status": "failed",
                        "reason": str(e),
                    }
                )
        return results
