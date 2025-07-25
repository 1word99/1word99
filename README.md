# Osmanli AI

## The Self-Evolving, Self-Repairing AI Assistant

Osmanli AI is an ambitious, multi-faceted AI project designed to be a self-evolving, self-repairing, and highly intelligent assistant. It integrates a wide array of advanced AI capabilities, from quantum computing and neuromorphic acceleration to ethical governance and deep code intelligence. The project aims to create an AI that can understand, analyze, and even repair its own codebase, learn from its environment, and interact with users through various interfaces.

## Features

*   **Self-Repairing & Self-Evolving Core**: Utilizes a sophisticated `AICortex` and `Surgeon` module for continuous analysis, problem detection, and autonomous code repair and optimization.
*   **Advanced AI Capabilities**: Integrates Quantum Neural Networks, Nanotech Simulation, Neuromorphic Acceleration, Neurosymbolic Reasoning, and more.
*   **Comprehensive Code Intelligence**: Features a `CodeAnalyzer`, `CodeGenerator`, and `LanguageServer` integration for deep understanding and manipulation of code.
*   **Multi-Interface Support**: Interact with Osmanli AI via Command-Line Interface (CLI), Graphical User Interface (GUI), Web Interface, and Voice.
*   **Neovim Integration**: Seamlessly connect with Neovim for real-time code analysis, completion, and automated fixes directly within your editor.
*   **Agent-Based Architecture**: Specialized agents (e.g., `CodeAgent`, `FinancialAgent`) handle domain-specific tasks.
*   **Plugin System**: Highly extensible architecture allowing for easy integration of new functionalities and external services.
*   **Security & Ethics**: Includes modules for Dark Web Monitoring, Quantum-Resistant Cryptography, Zero-Knowledge Provenance, and Ethical Governance.
*   **Chaos Engineering**: Built-in tools to test the system's resilience by simulating failures and observing self-healing capabilities.
*   **Knowledge Management**: Maintains a `KnowledgeBase` of past repairs and optimizations for continuous learning.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

*   Python 3.9+
*   `pip` (Python package installer)
*   `git` (for cloning the repository)
*   `nvim` (Neovim, if you plan to use the Neovim integration)
*   `gnome-terminal` (if you plan to launch Neovim from the CLI)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/osmanli-ai.git
    cd osmanli-ai
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    ```

4.  **Configure API Keys (Optional but Recommended):**
    Some features (e.g., LLM, financial data, web search) require API keys. Create a `.env` file in the project root and add your keys:

    ```
    # .env example
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    HF_API_TOKEN="YOUR_HUGGINGFACE_API_TOKEN"
    FINANCE_API_KEY="YOUR_FINANCE_API_KEY"
    STT_API_KEY="YOUR_SPEECH_TO_TEXT_API_KEY"
    WEB_SEARCH_API_KEY="YOUR_WEB_SEARCH_API_KEY"
    ENCRYPTION_KEY="YOUR_GENERATED_FERNET_KEY" # Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
    ```
    **Note**: For the `ENCRYPTION_KEY`, generate a strong key and keep it secure.

5.  **Initial Data Ingestion (for Quran module):**
    If you plan to use the Quran module, you might need to ingest data.
    ```bash
    python ingest_quran_data.py
    ```

### Running the AI

To start the Osmanli AI assistant, run the `main.py` script:

```bash
python main.py
```

This will initialize the `Orchestrator` and begin processing a predefined set of tasks.

### Running the CLI Interface

For interactive use, you can run the CLI interface:

```bash
python main.py --interface cli
```
*(Note: The `main.py` currently processes a task list. You might need to modify `main.py` to directly launch the CLI interface for continuous interaction, or integrate the CLI launch into the Orchestrator's task handling.)*

## Key Components & How to Use Them

### 1. Orchestrator (`osmanli_ai/core/orchestrator/orchestrator.py`)

The `Orchestrator` is the central task dispatcher. It receives high-level tasks and delegates them to the appropriate sub-systems.

**Usage Example (Conceptual - integrated within `main.py`):**

```python
from osmanli_ai.core.orchestrator.orchestrator import Orchestrator

orchestrator = Orchestrator()
orchestrator.handle_task("debug the system")
orchestrator.handle_task("visualize the codebase")
orchestrator.handle_task("nanotech_repair_simulation")
```

### 2. AICortex (`osmanli_ai/core/brain.py`)

The `AICortex` acts as the "brain" of the AI, coordinating continuous analysis, problem detection, and self-repair. It manages various core functionalities like `ProblemDetector`, `CodeAnalyzer`, `LLM` integration, `Memory`, and `PluginManager`.

**Usage Example (Conceptual - instantiated by `Orchestrator` or `Assistant`):**

```python
from osmanli_ai.core.brain import AICortex
from pathlib import Path

# Assuming project_root is defined
brain = AICortex(project_root=Path("."))
brain.start()
# ... AI operates continuously ...
brain.stop()
```

### 3. Assistant (`osmanli_ai/core/assistant.py`)

The `Assistant` is responsible for processing user queries, managing conversation memory, and interacting with plugins and agents.

**Usage Example (Conceptual - used by interfaces):**

```python
import asyncio
from osmanli_ai.core.assistant import Assistant
from osmanli_ai.core.configuration_manager import Config
from osmanli_ai.core.plugin_manager import PluginManager
from pathlib import Path

# Basic setup (simplified)
config = Config("config.json")
plugin_manager = PluginManager()
# plugin_manager.load_plugins() # Load plugins if not already done
assistant = Assistant(config, plugin_manager, project_root=Path("."))

async def interact():
    response = await assistant.process_query("What is the current stock price of AAPL?")
    print(f"Assistant: {response}")

# asyncio.run(interact())
```

### 4. Plugins (`osmanli_ai/plugins/`)

Plugins extend the AI's capabilities. They are dynamically loaded by the `PluginManager`.

**Key Plugins:**

*   **`HuggingFaceConversational`**: Provides general conversational abilities.
*   **`QuranPlugin`**: Accesses and processes Quranic knowledge.
*   **`BCIPlugin`**: (Brain-Computer Interface) Processes brainwave signals.
*   **`Code` Plugins (Copilot, Debugger)**: Assist with code generation, debugging, and refactoring.
*   **`Finance` Plugins (Stock)**: Retrieve and monitor stock information.
*   **`Media` Plugins (STT, TTS)**: Speech-to-Text and Text-to-Speech for voice interaction.
*   **`Vision` Plugins (OCR, Object Detection)**: Computer vision capabilities.
*   **`Web` Plugins (Search)**: Perform web searches.

**Usage (via `Assistant` or `RequestDispatcher`):**
Plugins are typically invoked indirectly through user queries routed by the `RequestDispatcher` or directly by other core components.

### 5. Agents (`osmanli_ai/agents/`)

Agents are specialized, autonomous components designed for specific domains or tasks.

**Key Agents:**

*   **`CodeAgent`**: Handles code analysis, generation, and refactoring.
*   **`FinancialAgent`**: Manages financial queries and stock monitoring.
*   **`SwarmManager`**: (Conceptual) For deploying and managing distributed agent swarms.

**Usage (via `AgentManager` and `RequestDispatcher`):**
Agents are managed by the `AgentManager` and their `process_task` methods are called when the `RequestDispatcher` identifies a query that an agent can handle.

### 6. CLI Interface (`osmanli_ai/interfaces/cli/cli.py`)

The command-line interface provides a textual way to interact with the AI.

**Usage:**

```bash
python main.py # (If main.py is configured to launch CLI)
# Or directly:
# python -c "import asyncio; from osmanli_ai.interfaces.cli.cli import run_cli; from osmanli_ai.core.assistant import Assistant; from osmanli_ai.core.configuration_manager import Config; from osmanli_ai.core.plugin_manager import PluginManager; from osmanli_ai.core.memory import ConversationMemory; from osmanli_ai.core.user_profile import UserProfile; from pathlib import Path; config = Config('config.json'); plugin_manager = PluginManager(); assistant = Assistant(config, plugin_manager, project_root=Path('.')); asyncio.run(run_cli(assistant, ConversationMemory(), config, user_profile=UserProfile('default_user', Path('./user_profiles'))))"
```
*(The direct command is long; it's recommended to configure `main.py` for easier CLI launch.)*

### 7. Neovim Integration (`nvim_integration/` and `osmanli_ai/utils/interprocess/`)

The Neovim integration allows the AI to provide real-time code intelligence, suggestions, and automated fixes directly within your Neovim editor.

**Setup:**

1.  **Ensure Neovim Bridge Server is Running**: The `NeovimBridgeServer` (from `osmanli_ai/utils/interprocess/neovim_bridge_server_util.py`) needs to be running. This is typically started as part of the main AI application.
2.  **Configure Neovim**: The Lua files in `nvim_integration/` are designed to be sourced by your Neovim configuration (`init.lua` or `init.vim`). You'll need to add lines like:
    ```lua
    -- In your Neovim init.lua
    require('nvim_integration.init')
    ```
    Refer to `nvim_integration/README.md` for detailed Neovim setup instructions.

**Usage:**
Once configured, the AI will provide diagnostics, code completions, and fix suggestions directly in Neovim. You can also send commands to the AI from Neovim.

### 8. Chaos Engineering (`osmanli_ai/chaos/orchestrator.py`)

The `ChaosOrchestrator` allows you to run experiments that introduce controlled failures to test the system's resilience and self-repair capabilities.

**Usage:**

```bash
python -m osmanli_ai.chaos.orchestrator
```
Then, you can call specific experiments:

```python
from osmanli_ai.chaos.orchestrator import ChaosOrchestrator

chaos_orchestrator = ChaosOrchestrator()

# Example: Mutilate a core code file
chaos_orchestrator.run_experiment("code_mutilation")

# Example: Corrupt the config file
chaos_orchestrator.run_experiment("config_corruption")

# IMPORTANT: Always run `chaos_orchestrator.cleanup()` after an experiment
# or restart the application to ensure files are restored.
```
**Warning**: Running chaos experiments can modify your project files. Always ensure you have a backup or are working in a disposable environment.

## Development & Contribution

### Running Tests

To run the unit tests, use `pytest`:

```bash
pytest
```

### Linting & Formatting

This project uses `ruff` for linting and formatting.

```bash
ruff check .
ruff format .
```

### Project Structure

Refer to `PROJECT_LAYOUT.md` for a detailed breakdown of the project's directory structure and the purpose of each module.

## License

[Specify your project's license here, e.g., MIT, Apache 2.0, etc.]

## Contact

For questions or support, please open an issue on the GitHub repository.
