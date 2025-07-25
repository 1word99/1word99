#!/usr/bin/env python3
"""
Osmanli AI Debug Launcher

This script provides a debug entry point for the Osmanli AI application with:
- Debug logging enabled
- Qt application context
- Exception handling
"""

import logging
import sys

from PyQt5.QtWidgets import QApplication, QMessageBox

# Configure logging before other imports
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("debug.log")],
)

logger = logging.getLogger(__name__)

try:
    # Local imports
    from main import OsmanliAI
except ImportError as e:
    logger.critical("Import failed: %s", e)
    sys.exit(1)


def main():
    """Main entry point for debug mode."""
    try:
        logger.info("Starting Osmanli AI in debug mode")

        # Create application instance
        app = QApplication(sys.argv)

        # Initialize main window
        window = OsmanliAI()
        window.setWindowTitle("Osmanli AI - Debug Mode")
        window.show()

        logger.info("Application started successfully")

        # Start event loop
        sys.exit(app.exec_())

    except Exception as e:
        logger.exception("Fatal error in debug mode")

        # Show error to user if GUI is available
        if "app" in locals():
            error_box = QMessageBox.critical(
                None,
                "Fatal Error",
                f"Application crashed:\n{str(e)}\n\nSee debug.log for details.",
            )
        sys.exit(1)


if __name__ == "__main__":
    main()
