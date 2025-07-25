import ast
import logging

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """
    A module for analyzing code files to extract structured information
    and identify potential issues or patterns.
    """

    def __init__(self):
        """Initializes the CodeAnalyzer."""
        logger.info("CodeAnalyzer initialized.")

    def analyze_python_file(self, file_content: str) -> dict:
        """
        Analyzes Python code content to extract information.
        Currently extracts imports, function names, and class names.
        """
        analysis_results = {"imports": [], "functions": [], "classes": [], "errors": []}
        try:
            tree = ast.parse(file_content)

            # Helper to get lines of code for a node
            def _get_node_lines(node):
                return node.end_lineno - node.lineno + 1

            # Helper to calculate cyclomatic complexity
            def _calculate_complexity(node):
                complexity = 0
                for sub_node in ast.walk(node):
                    if isinstance(
                        sub_node,
                        (
                            ast.If,
                            ast.For,
                            ast.While,
                            ast.AsyncFor,
                            ast.AsyncWith,
                            ast.With,
                            ast.FunctionDef,
                            ast.AsyncFunctionDef,
                            ast.ClassDef,
                            ast.comprehension,
                            ast.ExceptHandler,
                        ),
                    ):
                        complexity += 1
                return complexity

            # Helper to find unused imports
            class ImportVisitor(ast.NodeVisitor):
                def __init__(self):
                    self.imported_names = set()
                    self.used_names = set()
                    self.import_nodes = {}

                def visit_Import(self, node):
                    for alias in node.names:
                        self.imported_names.add(alias.name)
                        self.import_nodes[alias.name] = node
                    self.generic_visit(node)

                def visit_ImportFrom(self, node):
                    if node.module:
                        for alias in node.names:
                            imported_name = alias.name
                            # For 'from module import name', the imported name is 'name'
                            # For 'from module import name as alias', the imported name is 'alias'
                            self.imported_names.add(imported_name)
                            self.import_nodes[imported_name] = node
                    self.generic_visit(node)

                def visit_Name(self, node):
                    if isinstance(node.ctx, ast.Load):
                        self.used_names.add(node.id)
                    self.generic_visit(node)

                def visit_Attribute(self, node):
                    # Handle cases like 'module.function' where 'module' is used
                    if isinstance(node.ctx, ast.Load):
                        if isinstance(node.value, ast.Name):
                            self.used_names.add(node.value.id)
                    self.generic_visit(node)

            import_visitor = ImportVisitor()
            import_visitor.visit(tree)

            unused_imports = []
            for imported_name in import_visitor.imported_names:
                if imported_name not in import_visitor.used_names:
                    node = import_visitor.import_nodes[imported_name]
                    full_line = file_content.splitlines()[node.lineno - 1]
                    unused_imports.append(
                        {
                            "name": imported_name,
                            "line_number": node.lineno,
                            "full_line": full_line,
                        }
                    )
            analysis_results["unused_imports"] = unused_imports

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        analysis_results["imports"].append(n.name)
                elif isinstance(node, ast.ImportFrom):
                    analysis_results["imports"].append(node.module)
                elif isinstance(node, ast.FunctionDef):
                    analysis_results["functions"].append(
                        {
                            "name": node.name,
                            "loc": _get_node_lines(node),
                            "complexity": _calculate_complexity(node),
                            "start_line": node.lineno,
                        }
                    )
                elif isinstance(node, ast.ClassDef):
                    analysis_results["classes"].append(
                        {
                            "name": node.name,
                            "loc": _get_node_lines(node),
                            "start_line": node.lineno,
                        }
                    )
        except SyntaxError as e:
            analysis_results["errors"].append(f"Syntax Error: {e}")
            logger.error(f"Syntax error during code analysis: {e}")
        except Exception as e:
            analysis_results["errors"].append(f"General Error: {e}")
            logger.error(f"General error during code analysis: {e}")

        return analysis_results

    def analyze_file(self, file_path: str, file_content: str) -> dict:
        """
        Analyzes a file based on its extension.
        """
        if file_path.endswith(".py"):
            return self.analyze_python_file(file_content)
        # Add more file types here (e.g., .js, .ts, .json, .yaml)
        return {
            "message": "File type not supported for detailed analysis.",
            "file_path": file_path,
        }

    def self_test(self) -> bool:
        """Performs a self-test of the CodeAnalyzer component.
        Returns True if the component is healthy, False otherwise.
        """
        logger.info("Running self-test for CodeAnalyzer...")
        try:
            test_code = """
import os

def my_function():
    pass

class MyClass:
    def __init__(self):
        pass
"""
            results = self.analyze_python_file(test_code)

            if "os" not in results["imports"]:
                logger.error("CodeAnalyzer self-test failed: Missing import.")
                return False
            if not any(f["name"] == "my_function" for f in results["functions"]):
                logger.error("CodeAnalyzer self-test failed: Missing function.")
                return False
            if not any(c["name"] == "MyClass" for c in results["classes"]):
                logger.error("CodeAnalyzer self-test failed: Missing class.")
                return False
            if results["errors"]:
                logger.error(
                    f"CodeAnalyzer self-test failed: Errors found: {results['errors']}"
                )
                return False

            logger.info("CodeAnalyzer self-test passed.")
            return True
        except Exception as e:
            logger.error(f"CodeAnalyzer self-test failed: {e}")
            return False
