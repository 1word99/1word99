import logging

import requests

from osmanli_ai.plugins.base import BasePlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class Plugin(BasePlugin):
    """
    A plugin to fetch Quranic verses and translations from the specified Quran API.
    This API does not require any authentication.
    """

    def __init__(self, config):
        super().__init__(config)
        self.api_base_url = self.config.get("QURAN_API_URL", "http://127.0.0.1:3000")
        self.available_direct_translations = ["english", "arabic", "bengali", "urdu"]
        logger.info(f"QuranPlugin initialized. API URL: {self.api_base_url}")

    def initialize(self):
        super().initialize()
        logger.info("QuranPlugin activated.")

    def shutdown(self):
        super().shutdown()
        logger.info("QuranPlugin shut down.")

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="QuranPlugin",
            version="0.1.0",
            author="Osmanli AI",
            description="Provides access to Quranic verses and translations.",
            plugin_type=PluginType.KNOWLEDGE,
            capabilities=["quran_lookup", "random_quran_verse"],
            dependencies=[],
        )

    def get_plugin_type(self) -> PluginType:
        return PluginType.KNOWLEDGE

    def _make_request(self, endpoint: str):
        url = f"{self.api_base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error accessing Quran API at {url}: {e}")
            return None

    def get_ayah(
        self, surah_number: int, ayah_number: int, translation_lang: str = "english"
    ) -> str:
        if not (1 <= surah_number <= 114) or not (ayah_number >= 1):
            return (
                "Invalid Surah or Ayah number. Surah: 1-114, Ayah must be 1 or greater."
            )

        if translation_lang.lower() not in self.available_direct_translations:
            return (
                f"Error: '{translation_lang}' translation is not directly available with "
                f"verse requests. Choose from: {', '.join(self.available_direct_translations)}."
            )

        endpoint = f"/api/surah/{surah_number}/ayah/{ayah_number}"
        data = self._make_request(endpoint)

        if data and data.get("status") == "success":
            verse_data = data.get("data", {})
            arabic_text = verse_data.get("arabic_text", "Arabic text N/A")
            translation_text = verse_data.get(
                f"{translation_lang}_translation", "Translation N/A"
            )

            response_str = f"Quran (Surah {surah_number}, Ayah {ayah_number}):\n"
            response_str += f"Arabic: {arabic_text}\n"
            response_str += f"{translation_lang.capitalize()}: {translation_text}"
            return response_str
        elif data and data.get("status") == "error":
            return f"Error fetching Ayah: {data.get('message', 'Unknown API error.')}"
        else:
            return (
                f"Could not retrieve Surah {surah_number}, Ayah {ayah_number}. "
                "Please check the numbers or ensure the Quran API is running at "
                f"{self.api_base_url}."
            )

    def get_random_ayah(self, translation_lang: str = "english") -> str:
        if translation_lang.lower() not in self.available_direct_translations:
            return (
                f"Error: '{translation_lang}' translation is not directly available with "
                f"verse requests. Choose from: {', '.join(self.available_direct_translations)}."
            )

        endpoint = "/api/random"
        data = self._make_request(endpoint)

        if data and data.get("status") == "success":
            verse_data = data.get("data", {})
            surah_number = verse_data.get("surah_number", "N/A")
            ayah_number = verse_data.get("ayah_number", "N/A")
            arabic_text = verse_data.get("arabic_text", "Arabic text N/A")
            translation_text = verse_data.get(
                f"{translation_lang}_translation", "Translation N/A"
            )

            response_str = f"Random Ayah (Surah {surah_number}, Ayah {ayah_number}):\n"
            response_str += f"Arabic: {arabic_text}\n"
            response_str += f"{translation_lang.capitalize()}: {translation_text}"
            return response_str
        elif data and data.get("status") == "error":
            return f"Error fetching random Ayah: {data.get('message', 'Unknown API error.')}"
        else:
            return (
                "Could not retrieve a random Ayah. Please ensure the Quran API is running at "
                f"{self.api_base_url}."
            )

    def process(self, command: dict, context=None) -> str:
        action = command.get("action")
        translation_lang = command.get("lang", "english").lower()

        if action == "get_ayah":
            surah = command.get("surah")
            ayah = command.get("ayah")
            if isinstance(surah, int) and isinstance(ayah, int):
                return self.get_ayah(surah, ayah, translation_lang)
            else:
                return "Please provide valid integer 'surah' and 'ayah' numbers for 'get_ayah'."
        elif action == "get_random_ayah":
            return self.get_random_ayah(translation_lang)
        else:
            return "Unknown command for QuranPlugin. Available actions: 'get_ayah', 'get_random_ayah'."

    def get_capabilities(self) -> list[str]:
        return ["quran_lookup", "random_quran_verse"]
