"""
Provides a voice-based interface for the Osmanli AI assistant.
"""

import logging
import time

from osmanli_ai.interfaces.base_interface import BaseInterface  # Import BaseInterface

# --- Placeholder for STT/TTS Libraries ---
# You'll need to install libraries like:
# pip install SpeechRecognition  # For STT (e.g., Google Web Speech API, Sphinx, Whisper)
# pip install pyttsx3              # For TTS (offline)
# pip install gTTS                 # For TTS (online, Google Text-to-Speech)
# ------------------------------------------

try:
    pass
    # from gtts import gTTS # if using gTTS
    # import pyttsx3 # if using pyttsx3
except ImportError:
    sr = None
    # gTTS = None
    # pyttsx3 = None
    logging.warning("SpeechRecognition not installed. Voice features will be limited.")


# Set up logging for the Voice interface
logger = logging.getLogger(__name__)


class VoiceInterface(BaseInterface):  # Inherit from BaseInterface
    """
    Handles voice input (STT) and output (TTS) for the assistant.
    """

    def __init__(self, assistant, memory, config):
        super().__init__(
            assistant, memory, config
        )  # Call parent constructor for common initialization
        if sr is None:
            logger.error(
                "Speech recognition library not found. Please install 'SpeechRecognition'."
            )
            raise ImportError(
                "SpeechRecognition library is required for voice interface."
            )

        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        # self.tts_engine = pyttsx3.init() # Initialize pyttsx3 if using

        logger.info("Voice Interface initialized.")
        # You might want to adjust TTS voice, speed, etc. here
        # self.tts_engine.setProperty('rate', 150) # Speed
        # self.tts_engine.setProperty('voice', self.tts_engine.getVoices()[0].id) # Select a voice

    def speak(self, text):
        """Converts text to speech."""
        logger.info("Assistant speaking: %s", text)
        logger.info(f"Assistant (Speech placeholder): {text}")
        # Fallback if no TTS engine is ready

    def listen(self, timeout=5):
        """Listens for user speech and converts it to text."""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            self.speak("Listening...")
            logger.info("Listening for command...")
            try:
                audio = self.recognizer.listen(source, timeout=timeout)
                self.speak("Processing...")
                logger.info("Processing audio...")
                # Using Google Web Speech API for simplicity. Requires internet.
                text = self.recognizer.recognize_google(audio)
                logger.info("User said: %s", text)
                return text
            except sr.WaitTimeoutError:
                self.speak("Did not hear anything. Please try again.")
                logger.warning("%s", "Listening timed out.")
                return ""
            except sr.UnknownValueError:
                self.speak("Sorry, I could not understand audio.")
                logger.warning("Speech recognition could not understand audio.")
                return ""
            except sr.RequestError as e:
                self.speak(f"Could not request results from speech service; {e}")
                logger.error("Speech service error: %s", e)
                return ""

    async def run(self):
        """Runs the main voice interaction loop."""
        self.speak(
            "Osmanli AI Assistant voice mode active. Say 'exit' or 'quit' to end."
        )
        while True:
            try:
                user_query = self.listen()
                if user_query.lower() in ["exit", "quit"]:
                    self.speak("Goodbye!")
                    break
                if not user_query:
                    continue

                response = await self.assistant.process_query(user_query)
                self.speak(response)

            except (
                Exception
            ) as e:  # Catching broad exception to keep the voice loop running
                logger.error(
                    "An error occurred during voice interaction: %s", e, exc_info=True
                )
                self.speak("I encountered an error. Please try again.")
                time.sleep(1)  # Give a moment before trying to listen again


# Example of how main.py might call this
# async def run_voice(assistant, memory, config):
#     voice_app = VoiceInterface(assistant, memory, config)
#     await voice_app.run()
