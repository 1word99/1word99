import argparse
import logging
import threading
import time
import asyncio
from osmanli_ai.core.orchestrator.orchestrator import Orchestrator
from osmanli_ai.core.memory import ConversationMemory
from osmanli_ai.core.configuration_manager import Config
from osmanli_ai.core.user_profile import UserProfile
from osmanli_ai.core.assistant import Assistant
from osmanli_ai.core.plugin_manager import PluginManager
from osmanli_ai.core.brain import AICortex # Import AICortex
from pathlib import Path

# Configure logging for better visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define tasks outside the main block for potential reuse or modification
tasks = [
    "debug the system",
    "visualize the codebase",
    "evolve the genetic algorithm",
    "bootstrap a new project",
    "quantum_process",
    "digital_twin_analysis",
    "nanotech_repair_simulation",
    "dark_web_scan_for_threats",
    "exocortex_integration_demo",
    "bci_control_demo",
    "quantum_crypto_demo",
    "holographic_ar_integration_demo",
    "neuromorphic_offloading_demo",
    "distributed_swarm_intelligence_demo",
    "tda_analysis_demo",
    "ebpf_control_demo",
    "zk_provenance_demo",
    "plasma_physics_simulation_demo",
    "dark_matter_storage_demo",
    "rust_module_integration_demo",
    "metaverse_integration_demo",
    "formal_verification_demo",
    "self_replication_demo",
    "biofeedback_integration_demo",
    "neurosymbolic_reasoning_demo",
    "ethical_governance_demo",
    "unknown task"
]

async def main():
    parser = argparse.ArgumentParser(description='Osmanli AI Assistant')
    parser.add_argument('--interface', type=str, choices=['cli', 'gui', 'dashboard'],
                        help='Interface to launch (cli, gui, or dashboard)')
    args = parser.parse_args()

    # Initialize common components if an interface is requested
    if args.interface:
        app_config = Config("config.json")
        app_memory = ConversationMemory()
        app_user_profile = UserProfile("default_user", Path("user_profiles"))
        app_plugin_manager = PluginManager() # Initialize PluginManager
        
        # Initialize Orchestrator without starting visualization thread for interfaces
        # For dashboard, we will use AICortex as the brain
        if args.interface == 'dashboard':
            app_brain = AICortex(base_path=str(Path(".")))
        else:
            app_brain = Orchestrator(tasks=tasks, start_visualization_thread=False)

        # Initialize the full Assistant
        app_assistant = Assistant(
            config=app_config,
            plugin_manager=app_plugin_manager,
            quran_knowledge_base=None, # Assuming not needed for basic CLI, or initialized elsewhere
            brain=app_brain, # Pass the appropriate brain instance
            user_profile=app_user_profile,
            agent_manager=None, # Assuming not needed for basic CLI, or initialized elsewhere
            project_root=Path(".")
        )
        
        # Connect Neovim bridge if it's going to be used by the Assistant
        await app_assistant.connect_neovim_bridge()

        if args.interface == 'cli':
            try:
                from osmanli_ai.interfaces.cli.cli import run_cli
                logging.info("Launching CLI interface...")
                await run_cli(app_assistant, app_memory, app_config, user_profile=app_user_profile)
            except ImportError:
                logging.error("CLI interface module not found. Please ensure it's correctly implemented.")
            except Exception as e:
                logging.error(f"Error launching CLI interface: {e}")

        elif args.interface == 'gui':
            try:
                from osmanli_ai.interfaces.gui.app import OsmanliAIApp
                logging.info("Launching GUI interface...")
                app = OsmanliAIApp(app_user_profile)
                app.mainloop()
            except ImportError:
                logging.error("GUI interface module not found. Please ensure it's correctly implemented.")
            except Exception as e:
                logging.error(f"Error launching GUI interface: {e}")

        elif args.interface == 'dashboard':
            try:
                from osmanli_ai.interfaces.dashboard.app import DashboardApp
                logging.info("Launching Dashboard interface...")
                app = DashboardApp(app_assistant)
                await app.run_async() # Use run_async() and await it
            except ImportError:
                logging.error("Dashboard interface module not found. Please ensure it's correctly implemented.")
            except Exception as e:
                logging.error(f"Error launching Dashboard interface: {e}")

    else:
        logging.info("No interface specified. Running predefined tasks in background thread...")
        # Initialize Orchestrator with visualization thread for background tasks
        orchestrator = Orchestrator(tasks=tasks, start_visualization_thread=True)
        
        # Start task processing in a separate thread
        task_thread = threading.Thread(target=orchestrator.process_tasks)
        task_thread.daemon = True # Allow the main program to exit even if this thread is running
        task_thread.start()
        
        # Keep main thread alive for visualization or other background processes
        # This loop will prevent the main program from exiting immediately.
        try:
            while True:
                time.sleep(1) 
        except KeyboardInterrupt:
            logging.info("Main program interrupted. Exiting.")

if __name__ == "__main__":
    asyncio.run(main())