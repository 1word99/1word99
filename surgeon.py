import logging
import time
from pathlib import Path


from osmanli_ai.core.brain import AICortex

logger = logging.getLogger(__name__)


class Surgeon:
    """
    An intelligent agent that analyzes and repairs a codebase.
    """

    def __init__(self, project_root: Path, brain: AICortex):
        self.project_root = project_root
        self.brain = brain

    def operate(self, living: bool = False):
        """
        Performs a full surgical operation on the codebase.
        """
        logger.info("Starting surgical operation...")
        if living:
            logger.info(
                "Surgeon operating in living mode. Brain will continuously analyze and repair."
            )
            # In living mode, the brain's background workers handle continuous analysis and repair.
            # The surgeon just needs to keep the main thread alive or ensure the brain's threads are running.
            try:
                while True:
                    time.sleep(
                        10
                    )  # Keep surgeon alive, brain's threads are doing the work
            except KeyboardInterrupt:
                logger.info("Surgeon operation interrupted.")
        else:
            logger.info(
                "Surgeon operating in one-shot mode. Triggering brain's analysis."
            )
            # In one-shot mode, we can trigger an immediate analysis and wait for repairs to complete.
            # This would require a mechanism in AICortex to signal completion of a repair cycle.
            # For now, we'll just trigger the analysis and let the background workers run for a bit.
            # A more robust solution would involve waiting for the repair_worker_queue to be empty
            # or for a specific repair completion event.
            self.brain.analysis_worker(
                self.brain
            )  # Manually trigger one analysis cycle
            time.sleep(5)  # Give some time for repairs to be processed

        logger.info("Surgical operation complete.")

    def _run_a_fix_cycle(self):
        """
        Triggers the brain's analysis and repair cycle.
        """
        logger.info("Triggering brain's analysis and repair cycle...")
        # The brain's analysis_worker will detect problems and put them into the repair_worker_queue
        # The repair_worker will then pick them up and attempt to fix them.
        # We don't need to explicitly call fix_project here anymore.
        pass  # The actual work is done by the brain's background workers
