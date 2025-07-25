# osmanli_ai/utils/project_explorer.py
import logging
import os  # Needed for os.walk
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class ProjectExplorer:
    """
    Utility for exploring files and directories within a specified project path.
    """

    def __init__(self, base_path: Path):
        self.base_path = base_path.resolve()  # Resolve to absolute path
        if not self.base_path.is_dir():
            logger.warning(
                f"ProjectExplorer initialized with non-existent or non-directory path: {base_path}"
            )
        logger.info(f"ProjectExplorer initialized for base path: {self.base_path}")

    def list_files(
        self, relative_path: str = ".", include_dirs: bool = False
    ) -> List[Path]:
        """
        Lists files and optionally directories within a given relative path.

        Args:
            relative_path (str): Path relative to the base_path to start listing from.
            include_dirs (bool): If True, includes directories in the returned list.

        Returns:
            List[Path]: A list of Path objects for files/directories found.
        """
        full_path = self.base_path / relative_path
        if not full_path.is_dir():
            logger.warning(f"Attempted to list non-directory: {full_path}")
            return []

        found_items = []
        try:
            for item in full_path.iterdir():
                # Paths should be relative to base_path for consistent display/use by AI
                relative_item = item.relative_to(self.base_path)
                if item.is_file():
                    found_items.append(relative_item)
                elif item.is_dir() and include_dirs:
                    found_items.append(relative_item)
            logger.debug(f"Listed {len(found_items)} items in {full_path}")
        except PermissionError:
            logger.error(f"Permission denied when listing {full_path}")
        except Exception as e:
            logger.error(f"Error listing files in {full_path}: {e}", exc_info=True)
        return found_items

    def read_file_content(self, file_path: str, max_chars: int = 5000) -> str | None:
        """
        Reads the content of a file, limiting it to max_chars to prevent memory issues.
        The file_path can be absolute or relative to the explorer's base_path.

        Args:
            file_path (str): The path to the file.
            max_chars (int): Maximum number of characters to read from the file.

        Returns:
            str | None: The content of the file, or None if an error occurs.
        """
        abs_file_path = Path(file_path)
        if not abs_file_path.is_absolute():
            abs_file_path = self.base_path / file_path

        if not abs_file_path.is_file():
            logger.warning(
                f"Attempted to read non-existent or non-file: {abs_file_path}"
            )
            return None

        try:
            with open(abs_file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(max_chars)
                if len(content) == max_chars:
                    logger.warning(
                        f"File {abs_file_path} content truncated to {max_chars} characters."
                    )
                logger.debug(f"Read {len(content)} chars from {abs_file_path}")
                return content
        except Exception as e:
            logger.error(f"Error reading file {abs_file_path}: {e}", exc_info=True)
            return None

    def find_file(self, filename: str, start_path: str = ".") -> Path | None:
        """
        Recursively searches for a file within the base_path, starting from a relative path.
        """
        search_root = self.base_path / start_path
        if not search_root.is_dir():
            logger.warning(f"Search started from non-directory: {search_root}")
            return None

        for root, dirs, files in os.walk(search_root):
            if filename in files:
                return Path(root) / filename
        logger.info(
            f"File '{filename}' not found in '{search_root}' or its subdirectories."
        )
        return None

    def self_test(self) -> bool:
        """Performs a self-test of the ProjectExplorer component.
        Returns True if the component is healthy, False otherwise.
        """
        logger.info("Running self-test for ProjectExplorer...")
        import shutil
        import tempfile

        test_dir = None
        try:
            # 1. Create a temporary directory and dummy files
            test_dir = Path(tempfile.mkdtemp())
            (test_dir / "file1.txt").write_text("content1")
            (test_dir / "subdir").mkdir()
            (test_dir / "subdir" / "file2.txt").write_text("content2")

            # 2. Initialize ProjectExplorer with this temporary directory
            explorer = ProjectExplorer(test_dir)

            # 3. Test list_files
            files = explorer.list_files(include_dirs=True)
            if (
                len(files) != 2
                or Path("file1.txt") not in files
                or Path("subdir") not in files
            ):
                logger.error("ProjectExplorer self-test failed: list_files incorrect.")
                return False

            # 4. Test read_file_content
            content = explorer.read_file_content("file1.txt")
            if content != "content1":
                logger.error(
                    "ProjectExplorer self-test failed: read_file_content incorrect."
                )
                return False

            # 5. Test find_file
            found_file = explorer.find_file("file2.txt")
            if not found_file or found_file.name != "file2.txt":
                logger.error("ProjectExplorer self-test failed: find_file incorrect.")
                return False

            logger.info("ProjectExplorer self-test passed.")
            return True
        except Exception as e:
            logger.error(f"ProjectExplorer self-test failed: {e}")
            return False
        finally:
            # 6. Clean up temporary directory
            if test_dir and test_dir.exists():
                shutil.rmtree(test_dir)
