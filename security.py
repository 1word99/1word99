import logging
import subprocess

logger = logging.getLogger(__name__)


class SecurityScanner:
    """
    Scans the codebase for security vulnerabilities using bandit.
    """

    def scan(self, path: str) -> dict:
        """
        Scans the given path for vulnerabilities.
        """
        logger.info(f"Scanning {path} for vulnerabilities.")
        try:
            result = subprocess.run(
                ["bandit", "-r", path, "-f", "json"],
                capture_output=True,
                text=True,
            )
            return result.stdout
        except Exception as e:
            logger.error(f"Error running bandit: {e}")
            return {}
