# osmanli_ai/plugins/media/tts_plugin.py

from io import BytesIO

from gtts import gTTS

from osmanli_ai.core.exceptions import VoiceProcessingError
from osmanli_ai.plugins.base import BasePlugin, PluginMetadata, PluginType


class TTSPlugin(BasePlugin):
    def process(self, text: str, context: dict = None) -> bytes:
        """
        Converts text to audio data using Google Text-to-Speech.

        Args:
            text (str): The text to be converted to speech.
            context (dict, optional): Additional parameters like language, speaking rate.

        Returns:
            bytes: Raw audio data in MP3 format.
        """
        self.logger.info(
            f"TTSPlugin received text for speech generation: {text[:50]}..."
        )
        try:
            tts = gTTS(text=text, lang="en")  # Default to English
            audio_bytes_io = BytesIO()
            tts.write_to_fp(audio_bytes_io)
            audio_bytes_io.seek(0)
            self.logger.info("TTSPlugin successfully generated audio.")
            return audio_bytes_io.getvalue()
        except Exception as e:
            self.logger.error(f"TTSPlugin failed to generate audio: {e}")
            raise VoiceProcessingError(
                f"TTSPlugin failed to generate audio: {e}"
            ) from e

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="TTSPlugin",
            version="0.1.0",
            author="Osmanli AI",
            description="Converts text to speech using Google Text-to-Speech.",
            plugin_type=PluginType.MEDIA,
            capabilities=["text_to_speech"],
            dependencies=["gTTS"],
        )
