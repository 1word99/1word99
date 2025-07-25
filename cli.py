from typing import Optional
import speech_recognition as sr

from loguru import logger
from rich.console import Console

from osmanli_ai.core.user_profile import UserProfile
from osmanli_ai.interfaces.base_interface import BaseInterface
from osmanli_ai.utils.interprocess.neovim_bridge_client import NeovimBridgeClient
from osmanli_ai.plugins.media.stt_plugin import STTPlugin
from osmanli_ai.plugins.media.tts_plugin import TTSPlugin


class CLIInterface(BaseInterface):
    """
    Command-line interface for interacting with the Osmanli AI assistant.
    """

    def __init__(
        self,
        assistant,
        memory,
        config,
        voice_input_enabled=False,
        voice_output_enabled=False,
        neovim_bridge: Optional[NeovimBridgeClient] = None,
        stt_plugin: Optional[STTPlugin] = None,
        tts_plugin: Optional[TTSPlugin] = None,
        user_profile: Optional[UserProfile] = None,
    ):
        super().__init__(assistant, memory, config)
        self.assistant = assistant
        self.memory = memory
        self.config = config
        self.neovim_bridge = neovim_bridge
        self.voice_input_enabled = voice_input_enabled
        self.voice_output_enabled = voice_output_enabled
        self.stt_plugin = stt_plugin
        self.tts_plugin = tts_plugin
        self.user_profile = user_profile
        self.recognizer = sr.Recognizer() if self.voice_input_enabled else None
        self.microphone = sr.Microphone() if self.voice_input_enabled else None
        self.console = Console()
        logger.info("CLI Interface initialized.")

    async def run(self):
        """Runs the main command-line interaction loop."""
        self.console.print(
            "\nOsmanli AI Assistant Ready! Type 'exit' or 'quit' to end."
        )
        if self.voice_input_enabled:
            self.console.print("Voice input enabled. Press Enter and start speaking.")
        if self.voice_output_enabled:
            self.console.print("Voice output enabled.")
        self.console.print("-" * 50)

        while True:
            try:
                user_input = ""
                if (
                    self.voice_input_enabled
                    and self.stt_plugin
                    and self.recognizer
                    and self.microphone
                ):
                    self.console.print("Listening...")
                    with self.microphone as source:
                        self.recognizer.adjust_for_ambient_noise(source)
                        audio = self.recognizer.listen(source)
                    try:
                        user_input = self.stt_plugin.process(audio.frame_data)
                        self.console.print(f"You (voice): {user_input}")
                    except sr.UnknownValueError:
                        self.console.print(
                            "Could not understand audio, please try again."
                        )
                        continue
                    except sr.RequestError as e:
                        self.console.print(f"Speech recognition service error: {e}")
                        continue
                else:
                    user_input = self.console.input("You: ").strip()

                if user_input.lower() in ["exit", "quit"]:
                    self.console.print("Assistant: Goodbye!")
                    if self.neovim_bridge:
                        self.neovim_bridge.stop()
                    break

                if user_input.lower().startswith("set_preference "):
                    try:
                        parts = user_input.split(" ", 2)
                        if len(parts) == 3:
                            key = parts[1]
                            value = parts[2]
                            if self.user_profile:
                                self.user_profile.set(key, value)
                                self.console.print(
                                    f"Assistant: Preference '{key}' set to '{value}' for user '{self.user_profile.user_id}'."
                                )
                            else:
                                self.console.print(
                                    "Assistant: User profile not available."
                                )
                        else:
                            self.console.print(
                                "Assistant: Usage: set_preference <key> <value>"
                            )
                    except Exception as e:
                        self.console.print(f"Assistant: Error setting preference: {e}")
                    continue

                if not user_input:
                    continue

                response = await self.assistant.process_query(user_input)
                self.console.print(f"Assistant: {response}")

                if self.voice_output_enabled and response and self.tts_plugin:
                    audio_data = self.tts_plugin.process(response)
                    if audio_data:
                        import os
                        import tempfile

                        from pydub import AudioSegment
                        from pydub.playback import play

                        try:
                            with tempfile.NamedTemporaryFile(
                                delete=False, suffix=".mp3"
                            ) as fp:
                                fp.write(audio_data)
                                temp_filename = fp.name

                            audio_segment = AudioSegment.from_mp3(temp_filename)
                            play(audio_segment)
                            logger.info("Audio played successfully.")

                        except Exception as play_error:
                            logger.error(f"Error playing audio: {play_error}")
                        finally:
                            if "temp_filename" in locals() and os.path.exists(
                                temp_filename
                            ):
                                os.remove(temp_filename)

            except EOFError:
                self.console.print("\nAssistant: Exiting due to EOF. Goodbye!")
                if self.neovim_bridge:
                    self.neovim_bridge.stop()
                break
            except Exception as e:
                logger.error(
                    "An error occurred during interaction: %s", e, exc_info=True
                )
                self.console.print(
                    "Assistant: I encountered an error. Please try again."
                )

    async def run_dashboard(self):
        """Runs the widget-based dashboard."""
        from osmanli_ai.interfaces.cli.dashboard import OttomanCLI

        app = OttomanCLI(self.assistant)
        await app.run_async()


async def run_cli(
    assistant,
    memory,
    config,
    voice_input_enabled=False,
    voice_output_enabled=False,
    neovim_bridge=None,
    stt_plugin=None,
    tts_plugin=None,
    user_profile=None,
    dashboard_mode=False,
):
    """
    Runs the CLI interface.
    """
    cli_app = CLIInterface(
        assistant,
        memory,
        config,
        voice_input_enabled,
        voice_output_enabled,
        neovim_bridge,
        stt_plugin,
        tts_plugin,
        user_profile,
    )
    if dashboard_mode:
        await cli_app.run_dashboard()
    else:
        await cli_app.run()
