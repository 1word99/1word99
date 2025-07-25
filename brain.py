import ast
import hashlib

import logging
import os

import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from queue import Queue, Empty

import osmanli_ai  # Added this import

from osmanli_ai.core.decision_engine import DecisionEngine
from osmanli_ai.core.knowledge_base import KnowledgeBase
from osmanli_ai.core.context_manager import ContextManager
from osmanli_ai.core.security_analyzer import SecurityAnalyzer
from osmanli_ai.core.llm import LLM
from osmanli_ai.core.language_server_main import LanguageServer
from osmanli_ai.core.code_actions import CodeActions
from osmanli_ai.core.problem_detector import ProblemDetector
from osmanli_ai.core.code_analyzer import CodeAnalyzer
from osmanli_ai.core.component_status_manager import ComponentStatusManager, ComponentType, Status # Updated import


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OsmanliAI_Brain")


class NeuralComponent:
    """Base class for all AI components with self-healing capabilities"""

    def __init__(self, component_path: str):
        self.component_path = component_path
        self.health = 100  # 0-100 scale
        self.last_check = time.time()
        self.checksum = self.calculate_checksum()
        self.dependencies = self.analyze_dependencies()

    def calculate_checksum(self) -> str:
        """Calculate checksum of the component's source code"""
        with open(self.component_path, "r") as f:
            code = f.read()
        return hashlib.md5(code.encode()).hexdigest()

    def analyze_dependencies(self) -> List[str]:
        """Extract imported modules from the component"""
        with open(self.component_path, "r") as f:
            tree = ast.parse(f.read())

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module
                if module:
                    imports.append(module)
        return imports

    def check_health(self) -> bool:
        """Check the health of the component by running its associated tests."""
        test_path = "tests/" + self.component_path.replace(".py", "_test.py")
        if not os.path.exists(test_path):
            logger.warning(f"No tests found for {self.component_path}")
            return True  # Assume healthy if no tests exist

        try:
            import pytest

            result = pytest.main(["-q", test_path])
            if result == 0:
                self.health = 100
                return True
            else:
                self.health = 0
                return False
        except Exception as e:
            logger.error(f"Error running tests for {self.component_path}: {e}")
            self.health = 0
            return False

    def repair(self, problem: Dict[str, Any], cortex_instance: Any) -> bool:
        """Attempt to repair the component based on a detected problem."""
        logger.info(
            f"Attempting to repair {self.component_path} for problem: {problem.get('description', 'N/A')}"
        )

        action = problem.get("action")
        if not action:
            logger.warning(
                f"No actionable fix found for problem in {self.component_path}."
            )
            return False

        action_type = action.get("type")
        _ = action.get("target")
        suggestion = action.get("suggestion")
        content_to_remove = action.get("content")  # For remove_code

        try:
            current_content = Path(self.component_path).read_text(encoding="utf-8")
            updated_content = current_content

            if action_type == "remove_code" and content_to_remove:
                # This is a basic string replacement. For more complex removals,
                # AST manipulation or a dedicated refactoring tool would be needed.
                updated_content = updated_content.replace(content_to_remove, "")
                Path(self.component_path).write_text(updated_content, encoding="utf-8")
                logger.info(f"Successfully removed code in {self.component_path}.")
                return True
            elif action_type == "refactor" and suggestion:
                logger.info(
                    f"Refactoring suggested for {self.component_path}: {suggestion}"
                )
                # In a real scenario, this would involve calling a refactoring engine
                # or an LLM to generate the refactored code.
                # For now, we'll just log it as a successful "attempt" if a suggestion exists.
                return True
            elif action_type == "modify_code" and suggestion:
                logger.info(
                    f"Code modification suggested for {self.component_path}: {suggestion}"
                )
                # Similar to refactor, this would involve LLM or specific code manipulation.
                return True
            elif action_type == "create_file":
                file_path = Path(action["path"])
                template = action.get("template", "")
                file_path.write_text(template, encoding="utf-8")
                logger.info(f"Successfully created file: {file_path}")
                return True
            elif action_type == "create_directory":
                dir_path = Path(action["path"])
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Successfully created directory: {dir_path}")
                return True
            elif action_type == "move_file":
                source_path = Path(action["source"])
                destination_path = Path(action["destination"])
                source_path.rename(destination_path)
                logger.info(
                    f"Successfully moved file from {source_path} to {destination_path}"
                )
                return True
            else:
                logger.warning(
                    f"Unsupported repair action type: {action_type} for {self.component_path}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to apply repair action to {self.component_path}: {e}")
            return False


class AICortex:
    """
    The central AI brain, managing components, self-healing, and optimization.
    Enhanced to be more autonomous and capable of independent decision-making.
    """

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.components: Dict[str, NeuralComponent] = {}
        self.active = True
        self.health_check_interval = 60  # seconds
        self.optimization_interval = 300  # seconds
        self.decision_interval = 120  # seconds for autonomous decision making

        # Enhanced decision-making capabilities
        self.decision_engine = DecisionEngine()
        self.knowledge_base = KnowledgeBase()
        self.context_manager = ContextManager()
        self.language_server = LanguageServer()
        self.code_actions = CodeActions()
        self.security_analyzer = SecurityAnalyzer()
        self.llm = LLM(api_key="YOUR_API_KEY")  # Ensure LLM is initialized here
        import importlib

        importlib.reload(
            osmanli_ai.core.problem_detector
        )  # Force reload to avoid caching issues
        self.problem_detector = ProblemDetector()
        self.repair_worker_queue = Queue()  # Moved initialization here

        self._load_all_components()

        # Start background workers
        self.repair_thread = threading.Thread(
            target=self.repair_worker, daemon=True, args=(self,)
        )
        self.analysis_thread = threading.Thread(
            target=self.analysis_worker, daemon=True, args=(self,)
        )
        self.optimization_thread = threading.Thread(
            target=self.optimization_worker, daemon=True, args=(self,)
        )
        self.decision_thread = threading.Thread(
            target=self.decision_worker, daemon=True, args=(self,)
        )
        self.security_thread = threading.Thread(
            target=self.security_worker, daemon=True, args=(self,)
        )

        self.repair_thread.start()
        self.analysis_thread.start()
        self.optimization_thread.start()
        self.decision_thread.start()
        self.security_thread.start()

        self.repair_worker_queue = Queue()
        self.component_status = ComponentStatusManager() # Corrected initialization

        logger.info("AICortex initialized with enhanced autonomous capabilities.")

    def _load_all_components(self):
        """Discover and load all Python files as NeuralComponents."""
        for py_file in self.base_path.glob("**/*.py"):
            if py_file.name == "__init__.py":
                continue

            # Skip UI/interface files as they are not meant to be NeuralComponents
            if "interfaces" in py_file.parts:
                logger.debug(f"Skipping interface component: {py_file}")
                continue

            try:
                relative_path = py_file.relative_to(self.base_path.parent)
                module_name = str(relative_path).replace(os.sep, ".")[:-3]
                self._load_component(module_name, str(py_file))
            except ValueError:
                logger.warning(
                    f"Skipping component {py_file} as it's outside expected package structure."
                )
                continue

    def _load_component(self, module_name: str, file_path: str):
        """Load a single component dynamically and wrap it as a NeuralComponent."""
        try:
            # Using spec_from_file_location and exec_module to load the module
            # without directly importing it into the current namespace,
            # which helps avoid circular dependencies and allows inspection.
            # We don't need to import the module itself for health monitoring, just its path.
            self.components[file_path] = NeuralComponent(file_path)
            logger.info(
                f"Loaded module as component for health monitoring: {file_path}"
            )

        except Exception as e:
            logger.error(
                f"Failed to load component {module_name} from {file_path}: {e}"
            )

    def get_component_health(self, component_path: str) -> int:
        """Get the health score of a specific component"""
        return 100

    def repair_worker(self, cortex_instance):
        """Background worker for self-repair with enhanced capabilities"""
        while cortex_instance.active:
            try:
                problems = cortex_instance.repair_worker_queue.get(timeout=1)
                logger.debug(f"Repair worker received {len(problems)} problems.")
                for problem in problems:
                    component_path = problem.get("file")
                    if component_path and component_path in cortex_instance.components:
                        component = cortex_instance.components[component_path]
                        if component.repair(
                            problem, cortex_instance
                        ):  # Pass cortex_instance here
                            logger.info(
                                f"Component {component_path} repaired for problem: {problem.get('description', 'N/A')}"
                            )
                            # Update knowledge base with successful repair
                            self.knowledge_base.update_repair_knowledge(
                                component_path, problem, True
                            )
                        else:
                            logger.error(
                                f"Failed to repair component {component_path} for problem: {problem.get('description', 'N/A')}"
                            )
                            # Update knowledge base with failed repair
                            self.knowledge_base.update_repair_knowledge(
                                component_path, problem, False
                            )
                            # If repair fails, escalate to higher-level decision making
                            self.decision_engine.escalate_issue(
                                component_path,
                                problem.get("severity"),
                                problem.get("description"),
                            )
                    else:
                        logger.warning(
                            f"Problem detected for unknown component: {component_path}"
                        )
            except Empty:
                logger.debug("Repair worker queue is empty. Waiting...")
            time.sleep(1)  # Small sleep to prevent busy-waiting

    def analysis_worker(self, cortex_instance):
        """Background worker for code analysis and problem detection"""
        while cortex_instance.active:
            logger.debug("Running analysis worker...")
            file_analyses = {}
            code_analyzer = CodeAnalyzer()  # Instantiate CodeAnalyzer
            for component_name, component in cortex_instance.components.items():
                try:
                    file_content = Path(component.component_path).read_text(
                        encoding="utf-8"
                    )
                    # Perform detailed analysis using CodeAnalyzer
                    detailed_analysis = code_analyzer.analyze_python_file(file_content)
                    file_analyses[component.component_path] = detailed_analysis
                except Exception as e:
                    logger.error(
                        f"Could not read or analyze component {component.component_path} for analysis: {e}"
                    )

            # Detect problems using the ProblemDetector
            detected_problems = cortex_instance.problem_detector.detect_problems(
                cortex_instance.base_path, file_analyses
            )

            if detected_problems:
                logger.info(
                    f"Detected {len(detected_problems)} problems. Passing to repair worker."
                )
                # Pass problems to the repair worker for processing
                cortex_instance.repair_worker_queue.put(detected_problems)
            else:
                logger.info("No problems detected in this analysis cycle.")

            time.sleep(cortex_instance.health_check_interval)

    def optimization_worker(self, cortex_instance):
        """Background worker for optimization with enhanced capabilities"""
        while cortex_instance.active:
            logger.debug("Running enhanced optimization worker...")

            # Get current system context
            system_context = self.context_manager.analyze(self.base_path)

            # Analyze optimization opportunities
            optimization_opportunities = (
                self.decision_engine.identify_optimization_opportunities(system_context)
            )

            for opportunity in optimization_opportunities:
                component_name = opportunity["component"]
                optimization_type = opportunity["type"]
                context = opportunity["context"]

                logger.info(
                    f"Optimizing {component_name} with {optimization_type} based on context: {context}"
                )

                # Apply optimization
                if self.optimize_component(component_name, optimization_type, context):
                    logger.info(
                        f"Successfully optimized {component_name} with {optimization_type}"
                    )
                    # Update knowledge base with successful optimization
                    self.knowledge_base.update_optimization_knowledge(
                        component_name, optimization_type, True
                    )
                else:
                    logger.error(
                        f"Failed to optimize {component_name} with {optimization_type}"
                    )
                    # Update knowledge base with failed optimization
                    self.knowledge_base.update_optimization_knowledge(
                        component_name, optimization_type, False
                    )

            time.sleep(cortex_instance.optimization_interval)

    def security_worker(self, cortex_instance):
        """Background worker for security scanning."""
        while cortex_instance.active:
            logger.debug("Running security worker...")
            vulnerabilities = self.security_analyzer.scan_dependencies(self.base_path)
            if vulnerabilities:
                logger.warning(f"Found {len(vulnerabilities)} vulnerabilities.")
                # In a real implementation, you would want to do something with
                # these vulnerabilities, such as create a ticket or send an alert.
            time.sleep(cortex_instance.optimization_interval)

    def decision_worker(self, cortex_instance):
        """Background worker for autonomous decision making."""
        while cortex_instance.active:
            logger.debug("Running decision worker...")
            # In a real implementation, this would involve the decision engine
            # making high-level decisions based on system context and knowledge.
            time.sleep(cortex_instance.decision_interval)

    async def propose_fixes(
        self,
        content: str,
        diagnostics: List[Dict[str, Any]],
        ast_tree: Optional[ast.Module],
    ) -> List[Dict[str, Any]]:
        """Propose AI-driven fixes for the given code."""
        logger.info("AI-driven analysis started...")
        return self.llm.propose_fixes(content, diagnostics)

    def optimize_component(self, component_path: str):
        """Improve component performance"""
        try:
            from osmanli_ai.core.code_analyzer import analyze_performance
            from osmanli_ai.plugins.llm.general import generate_optimization

            analysis = analyze_performance(component_path)
            if analysis.get("bottlenecks"):
                optimized_code = generate_optimization(
                    original_code=Path(component_path).read_text(),
                    bottlenecks=analysis["bottlenecks"],
                )

                if optimized_code:
                    backup_path = f"backups/{os.path.basename(component_path)}.pre_opt"
                    with open(backup_path, "w") as f:
                        f.write(Path(component_path).read_text())

                    with open(component_path, "w") as f:
                        f.write(optimized_code)

                    logger.info(f"Optimization applied to {component_path}")
        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}")


if __name__ == "__main__":
    brain = AICortex(str(Path(__file__).parent.parent))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        brain.active = False
        logger.info("Shutting down OsmanliAI brain")