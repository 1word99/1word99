import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from osmanli_ai.core.code_analyzer import CodeAnalyzer

logger = logging.getLogger(__name__)


class ProblemDetector:
    """
    Analyzes project context and code analysis results to identify common problems
    and suggest solutions with actionable recommendations.
    """

    # Configuration constants
    LONG_FUNCTION_THRESHOLD = 50  # Lines of code
    LONG_CLASS_THRESHOLD = 100  # Lines of code
    COMPLEXITY_THRESHOLD = 10  # Cyclomatic complexity
    DUPLICATION_THRESHOLD = 5  # Number of duplicate lines
    MAX_FILE_SIZE_KB = 100  # KB

    def __init__(self):
        """Initializes the ProblemDetector with a set of predefined detectors."""
        self.code_analyzer = CodeAnalyzer()
        self.detectors = [
            self._detect_missing_ai_implementation,
            self._detect_incorrect_directory_structure,
            self._detect_code_quality_issues,
            self._detect_unused_imports,
            self._detect_large_files,
            self._detect_potential_bugs,
            self._detect_security_issues,
        ]
        logger.info(
            "ProblemDetector initialized with %d detectors", len(self.detectors)
        )

    def detect_problems(
        self, project_path: Path, file_analyses: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Detects problems within the project based on file analyses and project structure.

        Args:
            project_path: Root path of the project
            file_analyses: Dictionary of file analyses (path -> analysis data)

        Returns:
            List of detected problems with recommendations
        """
        problems = []

        for detector in self.detectors:
            try:
                problems.extend(detector(project_path, file_analyses))
            except Exception as e:
                logger.error(f"Detector {detector.__name__} failed: {str(e)}")

        return self._prioritize_problems(problems)

    def _detect_missing_ai_implementation(
        self, project_path: Path, file_analyses: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Detects missing AI implementation in basproject."""
        problems = []

        if project_path.name == "basproject":
            test_runner_path = str(project_path / "test_runner.py")
            if test_runner_path in file_analyses:
                analysis = file_analyses[test_runner_path]
                if "your_ai_module" in analysis.get("imports", []):
                    ai_module_path = project_path / "your_ai_module.py"
                    if not ai_module_path.exists():
                        problems.append(
                            {
                                "type": "Missing Implementation",
                                "severity": "High",
                                "file": str(test_runner_path),
                                "description": "The project imports 'your_ai_module' but the file doesn't exist.",
                                "recommendation": "Create 'your_ai_module.py' with a 'YourAI' class implementing a 'query' method.",
                                "action": {
                                    "type": "create_file",
                                    "path": str(ai_module_path),
                                    "template": "class YourAI:\n    def query(self, input):\n        # Implement your AI logic here\n        return input",
                                },
                            }
                        )
        return problems

    def _detect_incorrect_directory_structure(
        self, project_path: Path, file_analyses: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Detects incorrect project structure issues."""
        problems = []

        # Check test cases directory structure
        if (project_path / "basic_queries.json").exists():
            test_cases_dir = project_path / "test_cases"
            if not test_cases_dir.is_dir():
                problems.append(
                    {
                        "type": "Directory Structure",
                        "severity": "Medium",
                        "file": str(project_path),
                        "description": "Test case files should be in a 'test_cases' subdirectory.",
                        "recommendation": "Create a 'test_cases' directory and move test files into it.",
                        "action": {
                            "type": "create_directory",
                            "path": str(test_cases_dir),
                        },
                    }
                )
            elif not (test_cases_dir / "basic_queries.json").exists():
                problems.append(
                    {
                        "type": "File Organization",
                        "severity": "Medium",
                        "file": str(project_path / "basic_queries.json"),
                        "description": "Test case file is not in the 'test_cases' directory.",
                        "recommendation": "Move 'basic_queries.json' to the 'test_cases' directory.",
                        "action": {
                            "type": "move_file",
                            "source": str(project_path / "basic_queries.json"),
                            "destination": str(test_cases_dir / "basic_queries.json"),
                        },
                    }
                )

        return problems

    def _detect_code_quality_issues(
        self, project_path: Path, file_analyses: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Detects various code quality issues."""
        problems = []

        for file_path_str, analysis in file_analyses.items():
            if not file_path_str.endswith(".py"):
                continue

            # Long functions
            for func in analysis.get("functions", []):
                if func["loc"] > self.LONG_FUNCTION_THRESHOLD:
                    problems.append(
                        {
                            "type": "Code Quality",
                            "severity": "Medium",
                            "file": file_path_str,
                            "line": func["start_line"],
                            "description": f"Function '{func['name']}' is too long ({func['loc']} lines).",
                            "recommendation": "Refactor into smaller, single-responsibility functions.",
                            "action": {
                                "type": "refactor",
                                "target": func["name"],
                                "suggestion": "Consider breaking this function into smaller pieces.",
                            },
                        }
                    )

                if func.get("complexity", 0) > self.COMPLEXITY_THRESHOLD:
                    problems.append(
                        {
                            "type": "Code Complexity",
                            "severity": "High",
                            "file": file_path_str,
                            "line": func["start_line"],
                            "description": f"Function '{func['name']}' is too complex (cyclomatic complexity: {func['complexity']}).",
                            "recommendation": "Simplify the logic or break into smaller functions.",
                            "action": {
                                "type": "refactor",
                                "target": func["name"],
                                "suggestion": "Reduce nested conditions and loops.",
                            },
                        }
                    )

            # Large classes
            for cls in analysis.get("classes", []):
                if cls["loc"] > self.LONG_CLASS_THRESHOLD:
                    problems.append(
                        {
                            "type": "Code Quality",
                            "severity": "Medium",
                            "file": file_path_str,
                            "line": cls["start_line"],
                            "description": f"Class '{cls['name']}' is too large ({cls['loc']} lines).",
                            "recommendation": "Consider applying the Single Responsibility Principle and splitting the class.",
                            "action": {
                                "type": "refactor",
                                "target": cls["name"],
                                "suggestion": "Split this class into smaller, focused classes.",
                            },
                        }
                    )

            # Duplicate code
            for duplicate in analysis.get("duplicates", [])[
                :5
            ]:  # Limit to top 5 duplicates
                if duplicate["count"] > self.DUPLICATION_THRESHOLD:
                    problems.append(
                        {
                            "type": "Code Duplication",
                            "severity": "Medium",
                            "file": file_path_str,
                            "line": duplicate["start_line"],
                            "description": f"Duplicate code block ({duplicate['count']} lines repeated).",
                            "recommendation": "Extract the duplicate code into a shared function.",
                            "action": {
                                "type": "refactor",
                                "target": f"lines {duplicate['start_line']}-{duplicate['end_line']}",
                                "suggestion": "Create a helper function for this repeated logic.",
                            },
                        }
                    )

        return problems

    def _detect_unused_imports(
        self, project_path: Path, file_analyses: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Detects unused imports in Python files."""
        problems = []

        for file_path_str, analysis in file_analyses.items():
            if not file_path_str.endswith(".py"):
                continue

            file_content = Path(file_path_str).read_text(encoding="utf-8")
            detailed_analysis = self.code_analyzer.analyze_python_file(file_content)

            unused_imports = detailed_analysis.get("unused_imports", [])
            for imp in unused_imports:
                problems.append(
                    {
                        "type": "Unused Import",
                        "severity": "Low",
                        "file": file_path_str,
                        "line": imp["line_number"],
                        "description": f"Unused import: {imp['name']}",
                        "recommendation": "Remove unused imports to keep code clean.",
                        "action": {
                            "type": "remove_code",
                            "target": f"line {imp['line_number']}",
                            "content": imp["full_line"],
                        },
                    }
                )

        return problems

    def _detect_large_files(
        self, project_path: Path, file_analyses: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Detects files that are too large."""
        problems = []

        for file_path_str in file_analyses.keys():
            file_path = Path(file_path_str)
            try:
                size_kb = file_path.stat().st_size / 1024
                if size_kb > self.MAX_FILE_SIZE_KB:
                    problems.append(
                        {
                            "type": "File Size",
                            "severity": "Medium",
                            "file": file_path_str,
                            "description": f"File is too large ({size_kb:.1f} KB).",
                            "recommendation": "Consider splitting this file into smaller modules.",
                            "action": {
                                "type": "refactor",
                                "target": "file",
                                "suggestion": "Break this file into smaller, focused modules.",
                            },
                        }
                    )
            except OSError:
                continue

        return problems

    def _detect_potential_bugs(
        self, project_path: Path, file_analyses: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Detects potential bugs in the code."""
        problems = []

        for file_path_str, analysis in file_analyses.items():
            if not file_path_str.endswith(".py"):
                continue

            # Detect empty except blocks
            for issue in analysis.get("code_issues", []):
                if issue["type"] == "empty_except":
                    problems.append(
                        {
                            "type": "Potential Bug",
                            "severity": "High",
                            "file": file_path_str,
                            "line": issue["line"],
                            "description": "Empty except block silently catches all exceptions.",
                            "recommendation": "Specify the exception type to catch or add logging.",
                            "action": {
                                "type": "modify_code",
                                "target": f"line {issue['line']}",
                                "suggestion": "Replace with 'except Exception as e:' and handle properly",
                            },
                        }
                    )

        return problems

    def _detect_security_issues(
        self, project_path: Path, file_analyses: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Detects potential security issues."""
        problems = []

        for file_path_str, analysis in file_analyses.items():
            if not file_path_str.endswith(".py"):
                continue

            # Detect hardcoded passwords/secrets
            for issue in analysis.get("code_issues", []):
                if issue["type"] == "hardcoded_secret":
                    problems.append(
                        {
                            "type": "Security",
                            "severity": "Critical",
                            "file": file_path_str,
                            "line": issue["line"],
                            "description": "Potential hardcoded secret detected.",
                            "recommendation": "Use environment variables or secure configuration.",
                            "action": {
                                "type": "modify_code",
                                "target": f"line {issue['line']}",
                                "suggestion": "Replace with os.getenv('VAR_NAME') or config management",
                            },
                        }
                    )

        return problems

    def _prioritize_problems(
        self, problems: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Prioritizes problems by severity and type."""
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        return sorted(
            problems,
            key=lambda x: (severity_order.get(x.get("severity", "Low"), 3), x["type"]),
        )

    def suggest_fix(self, problem: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Provides detailed fix suggestion for a specific problem."""
        return problem.get("action")

    def self_test(self) -> bool:
        """Performs a self-test of the ProblemDetector component.
        Returns True if the component is healthy, False otherwise.
        """
        logger.info("Running self-test for ProblemDetector...")
        try:
            detector = ProblemDetector()

            # Test case 1: Missing AI implementation
            dummy_project_path = Path("/tmp/basproject")
            dummy_project_path.mkdir(exist_ok=True)
            (dummy_project_path / "test_runner.py").write_text("import your_ai_module")
            dummy_file_analyses = {
                str(dummy_project_path / "test_runner.py"): {
                    "imports": ["your_ai_module"]
                }
            }
            problems = detector.detect_problems(dummy_project_path, dummy_file_analyses)
            if not any("Missing Implementation" == p["type"] for p in problems):
                logger.error(
                    "ProblemDetector self-test failed: Missing AI implementation not detected."
                )
                return False

            # Clean up dummy project path
            import shutil

            shutil.rmtree(dummy_project_path)

            logger.info("ProblemDetector self-test passed.")
            return True
        except Exception as e:
            logger.error(f"ProblemDetector self-test failed: {e}")
            return False
