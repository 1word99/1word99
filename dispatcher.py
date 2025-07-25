# osmanli_ai/core/dispatcher.py
"""
Routes incoming user queries to the appropriate handler (plugin or internal logic).
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from loguru import logger

agent_interaction_logger = logger.bind(context="agent_interactions")


class RequestDispatcher:  # pylint: disable=too-few-public-methods
    """
    Routes incoming user queries to the appropriate handler (plugin or internal logic).
    This class acts as the "brain" for intent recognition and tool selection.
    It has access to the Assistant instance to leverage its plugins and core tools.
    Despite having few public methods, its complexity lies in the routing logic.
    """

    def __init__(self, assistant_instance):
        self.assistant = assistant_instance
        logger.info("RequestDispatcher initialized.")

    async def route(self, query: str, context: Dict[str, Any]) -> str:
        """
        Analyzes the query and context to determine the best handler.
        """
        query_lower = query.lower()

        if ";" in query:
            # Handle multilink requests
            links = query.split(";")
            responses = []
            for link in links:
                link = link.strip()
                if link:
                    response = await self.route(link, context)
                    responses.append(response)
            return "\n".join(responses)

        # Try handling as an internal command
        response = self._handle_internal_commands(query_lower)
        if response is not None:
            return response

        # Try handling as a Neovim request
        response = self._handle_neovim_requests(query_lower, query, context)
        if response is not None:
            return response

        # Try handling as a project request
        response = self._handle_project_requests(query_lower, query, context)
        if response is not None:
            return response

        # Handle confirmations (yes/no) if a pending action exists
        response = self._handle_confirmation_requests(query_lower)
        if response is not None:
            return response

        # Try handling as a Quran request
        response = self._handle_quran_requests(query_lower)
        if response is not None:
            return response

        # Try handling as a stock request
        response = self._handle_stock_requests(query_lower, query, context)
        if response is not None:
            return response

        # Try handling as an agent request
        response = await self._handle_agent_requests(query_lower, query, context)
        if response is not None:
            return response

        # --- Conversational AI (HuggingFaceConversationalPlugin) ---
        conversational_plugin = self.assistant.plugins.get_plugin(
            "HuggingFaceConversationalPlugin"
        )
        if conversational_plugin:
            # Format chat_history for the conversational plugin
            formatted_chat_history = []
            history_messages = self.assistant.memory.get_history(
                num_messages=5
            )  # Get recent messages

            # Pair up user and assistant messages
            user_message = None
            for msg in history_messages:
                if msg["role"] == "user":
                    user_message = msg["content"]
                elif msg["role"] == "assistant" and user_message is not None:
                    formatted_chat_history.append((user_message, msg["content"]))
                    user_message = None  # Reset for next pair

            return conversational_plugin.process(
                query, {"chat_history": formatted_chat_history}
            )

        # --- Default / Fallback Response (e.g., via Web Search or General LLM) ---
        web_search_plugin = self.assistant.plugins.get_plugin("WebSearchPlugin")
        if web_search_plugin:
            return web_search_plugin.process(query, context)

        general_llm_plugin = self.assistant.plugins.get_plugin("GeneralLLM")
        if general_llm_plugin and (
            "general_conversation" in general_llm_plugin.get_capabilities()
        ):
            full_context = self.assistant.memory.get_full_context_text(
                num_messages=5
            )  # Pass recent history
            llm_response = general_llm_plugin.process(
                query, {"conversation_history": full_context}
            )
            return llm_response
        return (
            "I am Osmanli AI. I'm still learning and improving my understanding. "
            f"I received your query: '{query}'. Can you rephrase or ask for "
            "something specific?"
        )

    def _handle_internal_commands(self, query_lower: str) -> str | None:
        """Handles direct commands or internal logic requests."""
        commands = {
            (
                "hello",
                "hi",
                "greetings",
            ): lambda: "Greetings, seeker of knowledge! How may I assist you today?",
            (
                "how are you",
            ): lambda: "I am an AI, so I don't experience feelings, but I am functioning optimally and ready to assist you!",
            (
                "what is your name",
            ): lambda: "I am Osmanli AI, your dedicated assistant.",
            (
                "time",
            ): lambda: f"The current time is {datetime.now().strftime('%H:%M:%S')}.",
            ("clear chat",): self._clear_chat,
            ("list plugins", "what can you do"): self._list_plugins,
        }

        for keywords, action in commands.items():
            if any(keyword in query_lower for keyword in keywords):
                return action()
        return None

    def _clear_chat(self) -> str:
        """Clears the conversation history."""
        self.assistant.memory.clear_history()
        return "Conversation history cleared. Ready for a fresh start!"

    def _list_plugins(self) -> str:
        """Lists the available plugins with their descriptions and capabilities."""
        plugins_info = []
        for name, plugin in self.assistant.plugins.get_all_plugins().items():
            metadata = plugin.get_metadata()
            capabilities = (
                ", ".join(metadata.capabilities) if metadata.capabilities else "None"
            )
            plugins_info.append(
                f"- **{metadata.name}** (v{metadata.version}): {metadata.description}\n  Capabilities: {capabilities}"
            )

        if plugins_info:
            return "I have the following plugins available:\n" + "\n".join(plugins_info)
        return "I currently have no plugins loaded. My capabilities are limited."

    def _handle_neovim_requests(
        self, query_lower: str, query: str, context: Dict[str, Any]
    ) -> str | None:
        """Handles requests related to Neovim interaction."""
        if not any(
            kw in query_lower
            for kw in [
                "neovim",
                "nvim",
                "code",
                "editor",
                "buffer",
                "insert text",
                "execute command",
            ]
        ):
            return None

        if not self.assistant.neovim_bridge_client.connect():
            return "I'm unable to connect to the Neovim bridge. Please ensure the Neovim bridge server is running."

        commands = {
            ("get current code", "read buffer"): self._get_neovim_buffer,
            ("insert text",): lambda: self._insert_neovim_text(context),
            ("execute nvim command",): lambda: self._execute_neovim_command(context),
            ("copilot",): lambda: self._run_copilot(query, context),
        }

        for keywords, action in commands.items():
            if any(keyword in query_lower for keyword in keywords):
                return action()

        return (
            "I can interact with Neovim. What specifically about code or the "
            "editor would you like to do? (e.g., 'get current code', "
            "'generate code', 'execute command')"
        )

    def _get_neovim_buffer(self) -> str:
        """Gets the current Neovim buffer content."""
        response = self.assistant.neovim_client.send_message(
            {"command": "get_current_buffer_content"}
        )
        return f"Neovim reports:\n```\n{response or 'No content or error getting content.'}\n```"

    def _insert_neovim_text(self, context: Dict[str, Any]) -> str:
        """Inserts text into the current Neovim buffer."""
        text_to_insert = context.get("text_to_insert")
        if not text_to_insert:
            return "No text provided to insert."
        response = self.assistant.neovim_bridge.send_message(
            {"command": "insert_text", "text": text_to_insert}
        )
        return (
            f"Neovim: Inserted text. Result: "
            f"{response or 'No specific response from Neovim.'}"
        )

    def _execute_neovim_command(self, context: Dict[str, Any]) -> str:
        """Executes a command in Neovim."""
        nvim_command = context.get("nvim_command")
        if not nvim_command:
            return "No Neovim command provided to execute."
        response = self.assistant.neovim_bridge.send_message(
            {"command": "execute_nvim_command", "nvim_command": nvim_command}
        )
        return (
            f"Neovim: Executed '{nvim_command}'. Result: "
            f"{response or 'No specific response from Neovim.'}"
        )

    def _run_copilot(self, query: str, context: Dict[str, Any]) -> str:
        """Runs the Copilot plugin."""
        copilot_plugin = self.assistant.plugins.get_plugin("CopilotPlugin")
        if copilot_plugin:
            return copilot_plugin.process(query, context)
        return (
            "The Copilot plugin is not available. Cannot assist with code generation."
        )

    def _handle_project_requests(
        self, query_lower: str, query: str, context: Dict[str, Any]
    ) -> str | None:
        """Handles requests related to project review or file system interaction."""
        if (
            "review project" in query_lower
            or "analyze code" in query_lower
            or "project structure" in query_lower
        ):
            # Check if context already provides a project path (e.g., from GUI's file dialog)
            project_path_str = context.get("project_path")
            if project_path_str:
                # Assistant handles the actual review, leveraging ProjectExplorer
                return self.assistant.conduct_project_review(Path(project_path_str))
            return (
                "To review a project, please tell me the path or use the 'Review Project' "
                "button in the GUI to select one."
            )
        return None  # Indicate no project request was matched

    def _handle_quran_requests(self, query_lower: str) -> str | None:
        """Handles requests related to Quran knowledge."""
        # Only proceed if the query explicitly mentions Quran
        if not any(
            kw in query_lower
            for kw in ["quran", "surah", "verse", "recite", "play quran"]
        ):
            return None  # Not a Quran-related query, let other handlers try

        if not self.assistant.quran:
            return "Quran knowledge base is not loaded or enabled in configuration."

        if "quran chapter" in query_lower:
            try:
                parts = query_lower.split()
                chapter_number = int(parts[parts.index("chapter") + 1])
                chapter_info = self.assistant.quran.get_chapter_info(chapter_number)
                if chapter_info:
                    return (
                        f"Chapter {chapter_number}: {chapter_info['surah_name']} "
                        f"({chapter_info['surah_name_ar']})\n"
                        f"Type: {chapter_info['type']}\n"
                        f"Total Verses: {chapter_info['total_verses']}\n"
                        f"Description: {chapter_info['description']}"
                    )
                return f"Chapter {chapter_number} not found."
            except (ValueError, IndexError):
                return (
                    "Please specify a valid chapter number (e.g., 'quran chapter 1')."
                )

        if "quran verse" in query_lower:
            try:
                parts = query_lower.split()
                chapter_index = parts.index("verse")
                chapter_number = int(parts[chapter_index + 1])
                verse_number = int(parts[chapter_index + 2])
                verse = self.assistant.quran.get_verse(chapter_number, verse_number)
                if verse:
                    return (
                        f"Chapter {verse['chapter_id']}:{int(str(verse['verse_id']).split('.')[1])}\n"
                        f"Arabic: {verse['content_ar']}\n"
                        f"Translation: {verse['translation_eng']}\n"
                        f"Transliteration: {verse['transliteration']}"
                    )
                return f"Verse {chapter_number}:{verse_number} not found."
            except (ValueError, IndexError):
                return "Please specify a valid chapter and verse number (e.g., 'quran verse 2 10')."

        if "quran search" in query_lower:
            try:
                keyword = query_lower.split("quran search", 1)[1].strip()
                if keyword:
                    results = self.assistant.quran.search_quran(keyword)
                    if results:
                        response = f"Found {len(results)} results for '{keyword}':\n"
                        for i, verse in enumerate(
                            results[:5]
                        ):  # Limit to 5 results for brevity
                            response += (
                                f"  {verse['chapter_id']}:{int(str(verse['verse_id']).split('.')[1])}: "
                                f"{verse['document']}\n"
                            )
                        if len(results) > 5:
                            response += "  ...and more. Please refine your search for more specific results.\n"
                        return response
                    return f"No results found for '{keyword}'."
                return "Please provide a keyword to search for (e.g., 'quran search God is one')."
            except IndexError:
                return "Please provide a keyword to search for (e.g., 'quran search God is one')."

        if "quran recite" in query_lower or "play quran" in query_lower:
            parts = query_lower.split()
            try:
                play_audio = "play" in parts

                if "chapter" in parts:
                    chapter_index = parts.index("chapter")
                    chapter_number = int(parts[chapter_index + 1])
                    chapter_info = self.assistant.quran.get_chapter_info(chapter_number)
                    if chapter_info:
                        response_text = (
                            f"Chapter {chapter_number}: {chapter_info['surah_name']} "
                            f"({chapter_info['surah_name_ar']})\n"
                            f"Type: {chapter_info['type']}\n"
                            f"Total Verses: {chapter_info['total_verses']}\n"
                            f"Description: {chapter_info['description']}"
                        )
                        if play_audio:
                            verses_to_play = []
                            for verse in chapter_info["verses"]:
                                verses_to_play.append(
                                    (chapter_number, verse["verse_number_in_chapter"])
                                )
                            self.assistant.quran.play_verses_audio(verses_to_play)
                            response_text += "\nPlaying audio for this chapter."
                        return response_text
                    return f"Chapter {chapter_number} not found."

                elif "recite" in parts and ("-" in query_lower or "," in query_lower):
                    # Handle verse ranges or multiple verses
                    recite_index = parts.index("recite")
                    chapter_number = int(parts[recite_index + 1])

                    if "-" in query_lower:
                        verse_range_str = parts[recite_index + 2]
                        start_verse, end_verse = map(int, verse_range_str.split("-"))
                        verses_to_play = [
                            (chapter_number, i)
                            for i in range(start_verse, end_verse + 1)
                        ]
                        response_text = f"Reciting verses {start_verse}-{end_verse} of Chapter {chapter_number}."
                    else:  # Assuming comma-separated
                        verse_numbers_str = parts[recite_index + 2]
                        verse_numbers = [int(v) for v in verse_numbers_str.split(",")]
                        verses_to_play = [(chapter_number, i) for i in verse_numbers]
                        response_text = f"Reciting verses {', '.join(map(str, verse_numbers))} of Chapter {chapter_number}."

                    if play_audio:
                        self.assistant.quran.play_verses_audio(verses_to_play)
                        response_text += "\nPlaying audio for selected verses."
                    return response_text

                elif "recite" in parts:
                    # Handle single verse recitation
                    recite_index = parts.index("recite")
                    chapter_number = int(parts[recite_index + 1])
                    verse_number = int(parts[recite_index + 2])
                    verse = self.assistant.quran.get_verse(chapter_number, verse_number)
                    if verse:
                        response_text = (
                            f"Chapter {verse['chapter_id']}:{int(str(verse['verse_id']).split('.')[1])}\n"
                            f"Arabic: {verse['content_ar']}\n"
                            f"Translation: {verse['translation_eng']}\n"
                            f"Transliteration: {verse['transliteration']}"
                        )
                        if play_audio:
                            self.assistant.quran.play_verse_audio(
                                chapter_number, verse_number
                            )
                            response_text += "\nPlaying audio for this verse."
                        return response_text
                    return f"Verse {chapter_number}:{verse_number} not found."

            except (ValueError, IndexError):
                return "Please specify a valid chapter and verse(s) for recitation (e.g., 'quran recite 1 1', 'quran recite 1 1-5', 'quran recite 1 1,3,5', 'quran recite chapter 1', or 'play quran chapter 1')."

        if "quran pause" in query_lower:
            return self.assistant.quran.pause_audio()

        if "quran resume" in query_lower:
            return self.assistant.quran.resume_audio()

        if "quran stop" in query_lower:
            return self.assistant.quran.stop_audio()

        return None  # Indicate no Quran request was matched

    def _handle_plugin_requests(
        self, query_lower: str, query: str, context: Dict[str, Any]
    ) -> str | None:
        """Handles requests that can be routed to a plugin based on keywords/capabilities."""
        # Check for Web Search
        if any(kw in query_lower for kw in ["search", "what is", "who is", "define"]):
            web_search_plugin = self.assistant.plugins.get_plugin("WebSearch")
            if (
                web_search_plugin
                and "web_search" in web_search_plugin.get_capabilities()
            ):
                search_term = (
                    query_lower.replace("search", "")
                    .replace("what is", "")
                    .replace("who is", "")
                    .replace("define", "")
                    .strip()
                )
                if search_term:
                    return web_search_plugin.process(search_term, context)
                return "Please provide a term for me to search."
            return (
                "The web search plugin is not available or doesn't support this query."
            )

        return None  # Indicate no plugin request was matched

    def _handle_confirmation_requests(self, query_lower: str) -> str | None:
        """Handles yes/no confirmations for pending actions."""
        if self.assistant.pending_action:
            if query_lower == "yes":
                action_type = self.assistant.pending_action["type"]
                if action_type == "resolve_basproject_issues":
                    project_path = Path(self.assistant.pending_action["project_path"])
                    self.assistant.pending_action = None  # Clear pending action
                    return self._resolve_basproject_issues(project_path)
                elif action_type == "run_basproject_tests":
                    command = self.assistant.pending_action["command"]
                    self.assistant.pending_action = None  # Clear pending action
                    return self._run_basproject_tests(command)
            elif query_lower == "no":
                self.assistant.pending_action = None
                return "Action cancelled."
        return None

    async def _handle_agent_requests(
        self, query_lower: str, query: str, context: Dict[str, Any]
    ) -> str | None:
        """
        Delegates requests to appropriate agents based on their capabilities.
        """
        if not self.assistant.agent_manager:
            return None

        for agent_name, agent in self.assistant.agent_manager.get_all_agents().items():
            if agent.can_handle_query(query):
                # For now, we'll assume the first agent that can handle the query is the one to use.
                # In a more advanced system, we might have a scoring mechanism or ask the user.
                if "analyze" in query_lower:
                    code_to_analyze = context.get("code", "")
                    if code_to_analyze:
                        task = {
                            "type": "analyze_code",
                            "payload": {"code": code_to_analyze},
                        }
                        result = await agent.process_task(task, context)
                        return f"Code Agent: {result.get('result', 'Analysis failed.')}"
                    else:
                        return "Please provide the code to analyze in the context."
                elif "generate" in query_lower:
                    prompt = query.replace("generate code", "").strip()
                    if prompt:
                        task = {"type": "generate_code", "payload": {"prompt": prompt}}
                        agent_interaction_logger.info(
                            f"Delegating 'generate_code' task to {agent_name} with prompt: {prompt[:50]}..."
                        )
                        result = await agent.process_task(task, context)
                        agent_interaction_logger.info(
                            f"Agent {agent_name} responded with: {result.get('result', '')[:50]}..."
                        )
                        return f"Code Agent: {result.get('result', 'Code generation failed.')}"
                    else:
                        return "Please provide a prompt for code generation."
                elif "generate" in query_lower:
                    prompt = query.replace("generate code", "").strip()
                    if prompt:
                        task = {"type": "generate_code", "payload": {"prompt": prompt}}
                        agent_interaction_logger.info(
                            f"Delegating 'generate_code' task to {agent_name} with prompt: {prompt[:50]}..."
                        )
                        result = await agent.process_task(task, context)
                        agent_interaction_logger.info(
                            f"Agent {agent_name} responded with: {result.get('result', '')[:50]}..."
                        )
                        return f"Code Agent: {result.get('result', 'Code generation failed.')}"
                    else:
                        return "Please provide a prompt for code generation."

        return None  # No agent handled the request

    def _handle_stock_requests(
        self, query_lower: str, query: str, context: Dict[str, Any]
    ) -> str | None:
        """Handles requests related to stock information."""
        stock_plugin = self.assistant.plugins.get_plugin("StockMonitorPlugin")
        if not stock_plugin:
            return "The Stock Monitor plugin is not available."

        if (
            "price of" in query_lower
            or "overview of" in query_lower
            or any(
                kw in query_lower for kw in ["stock", "monitor", "finance", "market"]
            )
        ):
            return stock_plugin.process(query, context)
        return None

    def _resolve_basproject_issues(self, project_path: Path) -> str:
        """Resolves known issues in the basproject, requiring terminal access."""
        response_messages = []
        test_cases_dir = project_path / "test_cases"

        # Create test_cases directory if it doesn't exist
        if not test_cases_dir.is_dir():
            logger.debug(f"Attempting to create directory: {test_cases_dir}")
            try:
                os.makedirs(test_cases_dir)
                response_messages.append(f"Created directory: {test_cases_dir}")
                logger.debug(f"Successfully created directory: {test_cases_dir}")
            except OSError as e:
                logger.error(f"Error creating directory {test_cases_dir}: {e}")
                return f"Error creating directory {test_cases_dir}: {e}"
        else:
            logger.debug(f"Directory already exists: {test_cases_dir}")

        # Move JSON files into test_cases directory
        json_files_to_move = ["basic_queries.json", "knowledge_questions.json"]
        for json_file in json_files_to_move:
            source_path = project_path / json_file
            destination_path = test_cases_dir / json_file
            logger.debug(f"Checking to move: {source_path} to {destination_path}")
            if source_path.exists() and not destination_path.exists():
                try:
                    os.rename(source_path, destination_path)
                    response_messages.append(f"Moved {json_file} to {test_cases_dir}")
                    logger.debug(
                        f"Successfully moved {source_path} to {destination_path}"
                    )
                except OSError as e:
                    response_messages.append(f"Error moving {json_file}: {e}")
                    logger.error(
                        f"Error moving {source_path} to {destination_path}: {e}"
                    )
            elif not source_path.exists():
                logger.warning(
                    f"Source file does not exist, skipping move: {source_path}"
                )
                response_messages.append(
                    f"Warning: {json_file} not found at source, skipping move."
                )
            elif destination_path.exists():
                logger.info(
                    f"Destination file already exists, skipping move: {destination_path}"
                )
                response_messages.append(
                    f"Info: {json_file} already exists in {test_cases_dir}, skipping move."
                )

        # Create a placeholder your_ai_module.py
        your_ai_module_path = project_path / "your_ai_module.py"
        if not your_ai_module_path.exists():
            try:
                with open(your_ai_module_path, "w") as f:
                    f.write(
                        """class YourAI:
    def query(self, input_text: str) -> str:
        return f"AI received: {input_text}"
"""
                    )
                response_messages.append(f"Created placeholder {your_ai_module_path}")
            except IOError as e:
                response_messages.append(f"Error creating {your_ai_module_path}: {e}")

        response_messages.append(
            "Basproject issues resolved. You can now run the tests."
        )
        response_messages.append(
            f"Would you like me to run 'python {project_path / 'test_runner.py'}' for you?"
        )
        self.assistant.pending_action = {
            "type": "run_basproject_tests",
            "command": f"python {project_path / 'test_runner.py'}",
        }
        return "\n".join(response_messages)

    def _run_basproject_tests(self, command: str) -> str:
        """Executes the basproject test runner in the terminal."""
        project_path = Path(
            command.split(" ")[1]
        ).parent  # Extract project path from command
        full_command = f"cd {project_path} && {command}"
        logger.info(f"Executing command: {full_command}")
        try:
            result = subprocess.run(
                full_command, shell=True, capture_output=True, text=True, check=True
            )
            return (
                f"Command output:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
        except subprocess.CalledProcessError as e:
            return (
                f"Error running command: {e}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
            )
        except Exception as e:
            return f"An unexpected error occurred while running the command: {e}"

    def self_test(self) -> bool:
        """Performs a self-test of the RequestDispatcher component.
        Returns True if the component is healthy, False otherwise.
        """
        logger.info("Running self-test for RequestDispatcher...")
        if not self.assistant:
            logger.error(
                "RequestDispatcher self-test failed: Assistant not initialized."
            )
            return False
        if not self.assistant.agent_manager:
            logger.error(
                "RequestDispatcher self-test failed: AgentManager not initialized."
            )
            return False
        logger.info("RequestDispatcher self-test passed.")
        return True
