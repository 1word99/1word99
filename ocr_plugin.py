import logging
from enum import Enum
from typing import Dict, List

from osmanli_ai.plugins.base import BasePlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class OCRLanguage(Enum):
    """Supported OCR languages with additional metadata"""

    ENGLISH = ("eng", "Latin")
    ARABIC = ("ara", "Arabic")
    TURKISH = ("tur", "Latin")
    # Add other languages as needed

    def __init__(self, code, script):
        self.code = code
        self.script = script


class OCRPlugin(BasePlugin):
    """Advanced OCR plugin with multiple engine support"""

    def __init__(self, config: Dict):
        super().__init__(config)
        self.engine = None
        self._initialized = False
        self.supported_languages = {lang.name: lang for lang in OCRLanguage}
        self.active_languages = self._validate_languages(
            config.get("languages", ["eng"])
        )

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="AdvancedOCR",
            version="2.3.0",
            author="Osmanli AI",
            description="Multi-engine OCR with advanced preprocessing",
            plugin_type=PluginType.VISION,
            capabilities=["text_extraction", "multi_language", "document_analysis"],
            dependencies=["Pillow>=9.0.0", "numpy", "pytesseract"],
            config_schema={
                "languages": {
                    "type": "list",
                    "items": {
                        "type": "str",
                        "options": [lang.code for lang in OCRLanguage],
                    },
                    "default": ["eng"],
                },
                "preprocess": {"type": "bool", "default": True},
            },
        )

    @classmethod
    def _validate_languages(cls, languages: List[str]) -> List[str]:
        """Validates and returns a list of supported language codes."""
        validated_langs = []
        for lang_code in languages:
            found = False
            for ocr_lang in OCRLanguage:
                if lang_code == ocr_lang.code:
                    validated_langs.append(lang_code)
                    found = True
                    break
            if not found:
                logger.warning(f"Unsupported OCR language code: {lang_code}. Skipping.")
        if not validated_langs:
            logger.warning("No valid OCR languages specified. Defaulting to English.")
            return [OCRLanguage.ENGLISH.code]
        return validated_langs
