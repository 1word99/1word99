from typing import Any, Dict, Optional

from loguru import logger

from osmanli_ai.core.agent import BaseAgent
from osmanli_ai.core.enums import ComponentType
from osmanli_ai.core.types import ComponentMetadata


class CodeAgent(BaseAgent):
    """
    A specialized agent for handling code-related tasks.
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        logger.info("CodeAgent initialized.")

    @classmethod
    def get_metadata(cls) -> ComponentMetadata:
        return ComponentMetadata(
            name="CodeAgent",
            version="0.1.0",
            description="Handles code analysis, generation, and refactoring tasks.",
            component_type=ComponentType.AGENT,
            author="Osmanli AI",
            capabilities=["code_analysis", "code_generation", "code_refactoring"],
        )

    async def process_task(
        self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processes a code-related task.

        Args:
            task (Dict[str, Any]): The task to process. Expected to have 'type' and 'payload'.
            context (Optional[Dict[str, Any]]): Additional context for the task.

        Returns:
            Dict[str, Any]: The result of the code task.
        """
        task_type = task.get("type")
        payload = task.get("payload", {})

        if task_type == "analyze_code":
            code = payload.get("code")
            if code:
                analysis_result = self._analyze_code(code)
                return {"status": "success", "result": analysis_result}
            else:
                return {"status": "error", "message": "No code provided for analysis."}
        elif task_type == "generate_code":
            prompt = payload.get("prompt")
            if prompt:
                generated_code = self._generate_code(prompt)
                return {"status": "success", "result": generated_code}
            else:
                return {
                    "status": "error",
                    "message": "No prompt provided for code generation.",
                }
        else:
            return {
                "status": "error",
                "message": f"Unknown code task type: {task_type}",
            }

    def _analyze_code(self, code: str) -> str:
        """
        Simulates code analysis.
        """
        logger.info("Analyzing code...")
        # Placeholder for actual code analysis logic
        return f"Analysis of code: '{code[:50]}...' completed. Found potential improvements."

    def _generate_code(self, prompt: str) -> str:
        """
        Simulates code generation.
        """
        logger.info("Generating code...")
        # Placeholder for actual code generation logic
        return (
            f"Generated code based on prompt: '{prompt[:50]}...'\n\n"
            "# Example generated code\n"
            "def hello_world():\n"
            '    print("Hello, World!")'
        )

    async def self_test(self) -> bool:
        """
        Performs a self-test of the CodeAgent component.
        """
        logger.info("Running self-test for CodeAgent...")
        try:
            # Test metadata
            metadata = self.get_metadata()
            if metadata.name != "CodeAgent":
                logger.error("CodeAgent self-test failed: Metadata name mismatch.")
                return False

            # Test process_task (analyze_code)
            task_analyze = {
                "type": "analyze_code",
                "payload": {"code": "print('hello')"},
            }
            result_analyze = await self.process_task(task_analyze)
            if (
                result_analyze["status"] != "success"
                or "Analysis of code" not in result_analyze["result"]
            ):
                logger.error("CodeAgent self-test failed: analyze_code task failed.")
                return False

            # Test process_task (generate_code)
            task_generate = {
                "type": "generate_code",
                "payload": {"prompt": "a python hello world function"},
            }
            result_generate = await self.process_task(task_generate)
            if (
                result_generate["status"] != "success"
                or "Generated code" not in result_generate["result"]
            ):
                logger.error("CodeAgent self-test failed: generate_code task failed.")
                return False

            # Test can_handle_query
            if not self.can_handle_query("analyze this code"):
                logger.error("CodeAgent self-test failed: can_handle_query failed.")
                return False

            logger.info("CodeAgent self-test passed.")
            return True
        except Exception as e:
            logger.error(f"CodeAgent self-test failed: {e}", exc_info=True)
            return False

    def can_handle_query(self, query: str) -> bool:
        """
        Determines if the CodeAgent can handle a given natural language query.
        """
        query_lower = query.lower()
        return any(
            keyword in query_lower
            for keyword in ["code", "analyze", "generate", "refactor", "debug"]
        )
