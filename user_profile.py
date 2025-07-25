import json
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from osmanli_ai.core.exceptions import UserProfileError


class UserProfile:
    """
    Manages user-specific data and preferences.
    Each user profile is stored as a JSON file.
    """

    def __init__(self, user_id: str, profile_dir: Path):
        self.user_id = user_id
        self.profile_dir = profile_dir
        self.profile_path = profile_dir / f"{user_id}.json"
        self.data: Dict[str, Any] = {}
        self._load_profile()

    def _load_profile(self):
        """Loads the user profile from a JSON file."""
        if self.profile_path.exists():
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                logger.info(
                    f"Profile for user '{self.user_id}' loaded from {self.profile_path}"
                )
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON for profile '{self.user_id}': {e}")
                self.data = {}  # Reset to empty if corrupted
                raise UserProfileError(
                    f"Corrupted profile for {self.user_id}: {e}"
                ) from e
            except Exception as e:
                logger.error(f"Error loading profile '{self.user_id}': {e}")
                self.data = {}
                raise UserProfileError(
                    f"Failed to load profile for {self.user_id}: {e}"
                ) from e
        else:
            logger.info(
                f"No existing profile found for user '{self.user_id}'. Creating new one."
            )
            self.data = {
                "user_id": self.user_id,
                "preferences": {},
                "history_summary": "",
            }
            self._save_profile()  # Save initial structure

    def _save_profile(self):
        """Saves the current user profile data to a JSON file."""
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.profile_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
            logger.info(
                f"Profile for user '{self.user_id}' saved to {self.profile_path}"
            )
        except Exception as e:
            logger.error(f"Error saving profile '{self.user_id}': {e}")
            raise UserProfileError(
                f"Failed to save profile for {self.user_id}: {e}"
            ) from e

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a value from the profile data."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        """Sets a value in the profile data and saves the profile."""
        self.data[key] = value
        self._save_profile()
        logger.debug(f"Set profile key '{key}' for user '{self.user_id}'.")

    def update_preferences(self, preferences: Dict[str, Any]):
        """Updates specific user preferences and saves the profile."""
        current_preferences = self.data.get("preferences", {})
        current_preferences.update(preferences)
        self.data["preferences"] = current_preferences
        self._save_profile()
        logger.info(f"Updated preferences for user '{self.user_id}'.")

    def get_preferences(self) -> Dict[str, Any]:
        """Retrieves all user preferences."""
        return self.data.get("preferences", {})

    def update_history_summary(self, summary: str):
        """Updates the summary of past interactions and saves the profile."""
        self.data["history_summary"] = summary
        self._save_profile()
        logger.debug(f"Updated history summary for user '{self.user_id}'.")

    def get_history_summary(self) -> str:
        """Retrieves the summary of past interactions."""
        return self.data.get("history_summary", "")

    def delete_profile(self):
        """Deletes the user's profile file."""
        if self.profile_path.exists():
            try:
                self.profile_path.unlink()
                logger.info(f"Profile file {self.profile_path} deleted.")
                return True
            except Exception as e:
                logger.error(f"Error deleting profile file {self.profile_path}: {e}")
                return False
        return False

    @staticmethod
    def list_profiles(profile_dir: Path) -> List[str]:
        """Lists all available user profile IDs."""
        if not profile_dir.is_dir():
            return []
        return [f.stem for f in profile_dir.glob("*.json") if f.is_file()]

    def self_test(self) -> bool:
        """Performs a self-test of the UserProfile component."""
        logger.info("Running self-test for UserProfile...")
        import shutil
        import tempfile

        test_profile_dir = None
        test_user_id = "test_user_123"
        try:
            test_profile_dir = Path(tempfile.mkdtemp())

            # Test profile creation and initial save
            profile = UserProfile(test_user_id, test_profile_dir)
            if not profile.profile_path.exists():
                logger.error("UserProfile self-test failed: Profile file not created.")
                return False
            if profile.get("user_id") != test_user_id:
                logger.error("UserProfile self-test failed: User ID mismatch.")
                return False

            # Test setting and getting data
            profile.set("favorite_color", "blue")
            if profile.get("favorite_color") != "blue":
                logger.error("UserProfile self-test failed: Set/get data failed.")
                return False

            # Test updating preferences
            profile.update_preferences({"theme": "dark", "notifications": True})
            prefs = profile.get_preferences()
            if prefs.get("theme") != "dark" or not prefs.get("notifications"):
                logger.error("UserProfile self-test failed: Update preferences failed.")
                return False

            # Test history summary
            profile.update_history_summary("User asked about weather.")
            if profile.get_history_summary() != "User asked about weather.":
                logger.error("UserProfile self-test failed: History summary failed.")
                return False

            # Test loading existing profile
            new_profile = UserProfile(test_user_id, test_profile_dir)
            if new_profile.get("favorite_color") != "blue":
                logger.error(
                    "UserProfile self-test failed: Loading existing profile failed."
                )
                return False

            # Test listing profiles
            listed_profiles = UserProfile.list_profiles(test_profile_dir)
            if test_user_id not in listed_profiles:
                logger.error("UserProfile self-test failed: Listing profiles failed.")
                return False

            # Test deleting profile
            if not profile.delete_profile():
                logger.error("UserProfile self-test failed: Deleting profile failed.")
                return False
            if profile.profile_path.exists():
                logger.error("UserProfile self-test failed: Profile file not deleted.")
                return False

            logger.info("UserProfile self-test passed.")
            return True
        except Exception as e:
            logger.error(f"UserProfile self-test failed: {e}", exc_info=True)
            return False
        finally:
            if test_profile_dir and test_profile_dir.exists():
                shutil.rmtree(test_profile_dir)
