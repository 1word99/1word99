# osmanli_ai/utils/security.py

import logging
import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Get the logger for this module
logger = logging.getLogger(__name__)


class SecureConfig:
    """
    Handles secure retrieval of sensitive configuration values,
    such as API tokens, potentially with encryption.
    """

    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        self.key = os.getenv("ENCRYPTION_KEY")
        if self.key:
            try:
                self.cipher = Fernet(self.key.encode())  # Key must be bytes
                logger.info("Encryption key loaded successfully.")
            except Exception as e:
                self.cipher = None
                logger.error(
                    f"Failed to initialize Fernet cipher with provided key: {e}"
                )
        else:
            self.cipher = None
            logger.warning(
                "ENCRYPTION_KEY environment variable not set. Sensitive data will not be decrypted."
            )

    def get_token(self, token_name: str) -> str:
        """
        Retrieves a token from environment variables.
        If an encryption key is set, attempts to decrypt the token.

        Args:
            token_name (str): The name of the environment variable holding the token.

        Returns:
            str: The decrypted token, or the raw token if no encryption key is set/valid,
                 or an empty string if the token is not found.
        """
        token = os.getenv(token_name)
        if token and self.cipher:
            try:
                # Tokens from .env are strings, encrypt/decrypt bytes
                return self.cipher.decrypt(token.encode()).decode()
            except Exception as e:
                logger.error(
                    f"Failed to decrypt token '{token_name}': {e}. Returning raw token."
                )
                return token  # Return raw token if decryption fails
        elif not token:
            logger.warning(f"Token '{token_name}' not found in environment variables.")
            return ""
        return token


def self_test() -> bool:
    """Performs a self-test of the SecureConfig component.
    Returns True if the component is healthy, False otherwise.
    """
    logger.info("Running self-test for SecureConfig...")
    import shutil
    import tempfile

    from dotenv import dotenv_values

    test_env_path = None
    original_env_values = dotenv_values()  # Save original .env values

    try:
        # 1. Setup: Create a temporary .env file with a test key and encrypted token
        test_env_dir = tempfile.mkdtemp()
        test_env_path = os.path.join(test_env_dir, ".env")

        # Generate a test key
        test_key = Fernet.generate_key().decode()
        cipher_test = Fernet(test_key.encode())
        encrypted_test_token = cipher_test.encrypt(b"my_secret_token").decode()

        with open(test_env_path, "w") as f:
            f.write(f"ENCRYPTION_KEY={test_key}\n")
            f.write(f"TEST_TOKEN={encrypted_test_token}\n")
            f.write("UNENCRYPTED_TOKEN=plain_text_token\n")

        # Temporarily set environment variable to point to the test .env
        os.environ["DOTENV_PATH"] = test_env_path

        # 2. Test SecureConfig with encryption
        secure_config_encrypted = SecureConfig()
        decrypted_token = secure_config_encrypted.get_token("TEST_TOKEN")
        if decrypted_token != "my_secret_token":
            logger.error("SecureConfig self-test failed: Decryption failed.")
            return False

        # 3. Test SecureConfig without encryption key
        with open(test_env_path, "w") as f:
            f.write("UNENCRYPTED_TOKEN=plain_text_token\n")
        secure_config_unencrypted = SecureConfig()
        unencrypted_token = secure_config_unencrypted.get_token("UNENCRYPTED_TOKEN")
        if unencrypted_token != "plain_text_token":
            logger.error(
                "SecureConfig self-test failed: Unencrypted token retrieval failed."
            )
            return False

        logger.info("SecureConfig self-test passed.")
        return True
    except Exception as e:
        logger.error(f"SecureConfig self-test failed: {e}")
        return False
    finally:
        # 4. Cleanup: Remove temporary .env file and restore original .env state
        if test_env_path and os.path.exists(test_env_path):
            shutil.rmtree(test_env_dir)
        if "DOTENV_PATH" in os.environ:
            del os.environ["DOTENV_PATH"]
        # Restore original .env values
        for key, value in original_env_values.items():
            os.environ[key] = value
