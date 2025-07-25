"""
osmanli_ai/core/ai_fixer.py
Complete AI-powered code repair system
"""

import ast
import fnmatch
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set  # All required imports

logger = logging.getLogger(__name__)


class AICodeFixer:
    """Comprehensive code repair system with virtualenv safety"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.package_name = "osmanli_ai"
        self.fixed_files: Set[Path] = set()

        # Configure exclusions
        self.exclude_patterns = [
            "*/.venv/*",
            "*/venv/*",
            "*/.virtualenv/*",
            "*/__pycache__/*",
            "*/site-packages/*",
            "*/.git/*",
            "*/.mypy_cache/*",
        ]

        # Initialize fixers
        self.fixers = {
            "imports": self.fix_imports,
            "syntax": self.fix_syntax_errors,
            "neovim": self.neovim_integration_fix,
        }
        self.neovim_available = self._check_neovim()

    def _check_neovim(self) -> bool:
        """Check if Neovim is available for advanced fixes"""
        try:
            subprocess.run(
                ["nvim", "--version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("Neovim not available - some fixes will be limited")
            return False

    def should_exclude(self, filepath: Path) -> bool:
        """Check if file should be excluded from repairs"""
        path_str = str(filepath)
        return any(
            fnmatch.fnmatch(path_str, pattern) for pattern in self.exclude_patterns
        )

    def fix_imports(self, filepath: Path) -> List[Dict[str, Any]]:
        """Fix relative and absolute imports in a file and return proposals."""
        if self.should_exclude(filepath):
            return []

        proposals = []
        try:
            content = filepath.read_text(encoding="utf-8")
            tree = ast.parse(content)
            lines = content.splitlines()

            # Simple unused import detection (can be expanded)
            imported_names = set()
            used_names = set()

            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        imported_names.add(alias.name)
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)

            unused_imports = imported_names - used_names

            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        if alias.name in unused_imports:
                            line_num = node.lineno
                            old_text = lines[line_num - 1]  # 1-indexed to 0-indexed
                            new_text = ""
                            proposals.append(
                                {
                                    "filepath": str(filepath),
                                    "line": line_num,
                                    "description": f"Remove unused import: {old_text.strip()}",
                                    "old_text": old_text,
                                    "new_text": new_text,
                                }
                            )

            return proposals

        except Exception as e:
            logger.error(f"Failed to fix imports in {filepath}: {e}")
            return []

    def _resolve_relative_import(
        self, filepath: Path, node: ast.ImportFrom
    ) -> Optional[str]:
        """Convert relative import to absolute path"""
        if not node.module:
            return None

        rel_path = filepath.relative_to(self.project_root).parent
        parts = list(rel_path.parts)  # Convert to list to allow modification

        # If the first part is already the package name, remove it to avoid redundancy
        if parts and parts[0] == self.package_name:
            parts.pop(0)

        # Construct the absolute import path
        if parts:
            return f"{self.package_name}.{'.'.join(parts)}.{node.module}"
        else:
            return f"{self.package_name}.{node.module}"

    def fix_syntax_errors(self, filepath: Path) -> List[Dict[str, Any]]:
        """Basic syntax error detection and proposal for manual correction."""
        if self.should_exclude(filepath):
            return []

        proposals = []
        try:
            content = filepath.read_text(encoding="utf-8")
            try:
                ast.parse(content)
            except SyntaxError as e:
                logger.warning(f"Syntax error in {filepath}: {e}")
                proposals.append(
                    {
                        "filepath": str(filepath),
                        "line": e.lineno,
                        "column": e.offset or 0,
                        "description": f"Syntax Error: {e.msg}. Please review manually.",
                        "old_text": content.splitlines()[e.lineno - 1]
                        if e.lineno
                        else "",
                        "new_text": "",  # No automatic fix for general syntax errors
                        "severity": "error",
                    }
                )
            return proposals

        except Exception as e:
            logger.error(f"Failed to check syntax in {filepath}: {e}")
            return []

    def neovim_integration_fix(self, filepath: Path) -> List[Dict[str, Any]]:
        """Use Neovim's LSP for advanced fixes"""
        if not self.neovim_available or self.should_exclude(filepath):
            return []

        try:
            with tempfile.NamedTemporaryFile(mode="w+", suffix=".py"):
                result = subprocess.run(
                    [
                        "nvim",
                        "--headless",
                        "--noplugin",
                        "-c",
                        f"e {filepath}",
                        "-c",
                        "lua vim.lsp.buf.format()",
                        "-c",
                        "lua vim.lsp.buf.code_action()",
                        "-c",
                        "wq",
                    ],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    logger.error(f"Neovim failed: {result.stderr}")
                    return []

                return []  # No direct proposals from this, but it might apply fixes directly

        except Exception as e:
            logger.error(f"Neovim integration failed: {e}")
            return []

    def fix_project(self) -> Dict[str, Any]:
        """Run all fixers on the project and return aggregated proposals."""
        all_proposals = []
        for fixer_name, fixer_func in self.fixers.items():
            logger.info(f"Running fixer: {fixer_name}")
            for filepath in self.project_root.rglob("*.py"):
                proposals = fixer_func(filepath)
                if proposals:
                    all_proposals.extend(proposals)
        return {"proposals": all_proposals}
