# osmanli_ai/core/code_actions.py

import ast


class CodeActions:
    """
    Provides context-aware code suggestions and refactoring patterns.

    - Suggests refactoring opportunities.
    - Provides error correction strategies.
    - Offers code optimization recipes.
    """

    def __init__(self):
        pass

    def suggest_refactoring(self, code: str) -> str:
        """
        Suggests refactoring for the given code by analyzing the AST.
        Identifies long functions as a simple refactoring opportunity.
        """
        try:
            tree = ast.parse(code)
            suggestions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_length = node.end_lineno - node.lineno
                    if function_length > 50:  # Arbitrary threshold for a long function
                        suggestions.append(
                            f"Function '{node.name}' at line {node.lineno} is long ({function_length} lines). Consider refactoring it."
                        )

            return (
                "\n".join(suggestions)
                if suggestions
                else "No specific refactoring suggestions found."
            )
        except SyntaxError as e:
            return f"Syntax error, cannot provide refactoring suggestions: {e}"

    def suggest_optimizations(self, code: str) -> str:
        """
        Suggests optimizations for the given code by analyzing the AST.
        Identifies for-loops that can be converted to list comprehensions.
        """
        try:
            tree = ast.parse(code)
            suggestions = []

            class ListCompVisitor(ast.NodeVisitor):
                def visit_For(self, node: ast.For):
                    # Check for a simple for loop that appends to a list
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Expr):
                        call = node.body[0].value
                        if (
                            isinstance(call, ast.Call)
                            and isinstance(call.func, ast.Attribute)
                            and call.func.attr == "append"
                        ):
                            suggestions.append(
                                f"Consider using a list comprehension for the loop at line {node.lineno}."
                            )
                    self.generic_visit(node)

            ListCompVisitor().visit(tree)
            return (
                "\n".join(suggestions)
                if suggestions
                else "No specific optimization suggestions found."
            )
        except SyntaxError as e:
            return f"Syntax error, cannot provide optimization suggestions: {e}"
