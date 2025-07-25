import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class SkillManager:
    """
    Manages and executes predefined skills or frequent tasks.
    Skills can be thought of as specialized functions that the AI can perform.
    """

    def __init__(self):
        self._skills: Dict[str, Callable] = {}
        logger.info("SkillManager initialized.")

    def register_skill(self, name: str, skill_func: Callable) -> None:
        """
        Registers a new skill with the manager.

        Args:
            name: The unique name of the skill.
            skill_func: The function that implements the skill's logic.
        """
        if name in self._skills:
            logger.warning(f"Skill '{name}' already registered. Overwriting.")
        self._skills[name] = skill_func
        logger.debug(f"Skill '{name}' registered.")

    def execute_skill(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Executes a registered skill.

        Args:
            name: The name of the skill to execute.
            *args: Positional arguments to pass to the skill function.
            **kwargs: Keyword arguments to pass to the skill function.

        Returns:
            The result of the skill function.

        Raises:
            ValueError: If the skill is not found.
        """
        skill_func = self._skills.get(name)
        if not skill_func:
            logger.error(f"Skill '{name}' not found.")
            raise ValueError(f"Skill '{name}' not found.")

        logger.info(f"Executing skill '{name}'.")
        try:
            return skill_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing skill '{name}': {e}")
            raise

    def list_skills(self) -> List[str]:
        """
        Returns a list of all registered skill names.
        """
        return list(self._skills.keys())

    def self_test(self) -> bool:
        """Performs a self-test of the SkillManager component."""
        logger.info("Running self-test for SkillManager...")
        try:
            manager = SkillManager()

            def dummy_skill(a, b):
                return a + b

            manager.register_skill("add_numbers", dummy_skill)

            # Test skill execution
            result = manager.execute_skill("add_numbers", 5, 3)
            if result != 8:
                logger.error(
                    "SkillManager self-test failed: Skill execution incorrect."
                )
                return False

            # Test listing skills
            skills = manager.list_skills()
            if "add_numbers" not in skills:
                logger.error("SkillManager self-test failed: Skill not listed.")
                return False

            # Test non-existent skill
            try:
                manager.execute_skill("non_existent_skill")
                logger.error(
                    "SkillManager self-test failed: Did not raise error for non-existent skill."
                )
                return False
            except ValueError:
                pass  # Expected

            logger.info("SkillManager self-test passed.")
            return True
        except Exception as e:
            logger.error(f"SkillManager self-test failed: {e}")
            return False
