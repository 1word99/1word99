import logging
import json
import google.generativeai as genai


logger = logging.getLogger(__name__)


class LLM:
    """
    Handles communication with the Gemini API.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-pro")

    def propose_fixes(self, code: str, diagnostics: list) -> list:
        """
        Proposes fixes for the given code and diagnostics.
        """
        logger.info("Proposing fixes using Gemini API.")
        # This is a simplified example. A real implementation would need to
        # construct a more sophisticated prompt.
        prompt = f"""You are an AI assistant specialized in refactoring Python code. Your task is to analyze the provided code and diagnostics, and then propose refactoring changes.\n\nHere is the Python code:\n\n```python\n{code}\n```\n\nHere are the diagnostics/problems identified:\n\n```json\n{json.dumps(diagnostics, indent=2)}\n```\n
Based on these, provide a list of refactoring suggestions. Each suggestion should be a JSON object with the following keys:\n- `old_text`: The exact string of code to be replaced.\n- `new_text`: The exact string of code to replace `old_text` with.\n\nExample of expected JSON output:\n```json\n[\n  {{\"old_text\": \"def old_function():\\n    pass\", \"new_text\": \"def new_function():\\n    pass\"}},\n  {{\"old_text\": \"# old comment\", \"new_text\": \"# new comment\"}}\n]\n```\n\nProvide only the JSON array as your response, without any additional text or explanation.\n"""
        try:
            response = self.model.generate_content(prompt)
            # Attempt to parse the response as JSON. The LLM should return valid JSON.
            return json.loads(response.text)
        except Exception as e:
            logger.error(
                f"Error communicating with Gemini API or parsing response: {e}"
            )
            return []
