# osmanli_ai/utils/optimization.py

import logging

import torch

logger = logging.getLogger(__name__)


def optimize_model(model):
    """
    Applies common PyTorch optimizations to a model.
    Utilizes torch.compile for PyTorch 2.0+ and gradient checkpointing.

    Args:
        model: The PyTorch model to optimize.

    Returns:
        The optimized model.
    """
    try:
        if hasattr(torch, "compile"):
            model = torch.compile(model)  # PyTorch 2.0 compiler
            logger.info("Model compiled with torch.compile.")
        else:
            logger.warning(
                "torch.compile not available (requires PyTorch 2.0+). Skipping compilation."
            )
    except Exception as e:
        logger.error(f"Error during model compilation: {e}")

    if hasattr(model, "enable_input_require_grads"):
        try:
            model.enable_input_require_grads()
            logger.info("Model input require grads enabled.")
        except Exception as e:
            logger.warning(f"Could not enable input require grads: {e}")

    if hasattr(model, "gradient_checkpointing_enable"):
        try:
            model.gradient_checkpointing_enable()
            logger.info("Model gradient checkpointing enabled.")
        except Exception as e:
            logger.warning(f"Could not enable gradient checkpointing: {e}")

    return model


def cleanup_memory():
    """
    Cleans up GPU memory cache if CUDA is available.
    """
    if torch.cuda.is_available():
        try:
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
            logger.info("CUDA memory cache cleared.")
        except Exception as e:
            logger.error(f"Error during CUDA memory cleanup: {e}")
    else:
        logger.info("CUDA not available, skipping memory cleanup.")


def self_test() -> bool:
    """Performs a self-test of the optimization utilities.
    Returns True if the components are healthy, False otherwise.
    """
    logger.info("Running self-test for optimization.py...")
    try:
        # Test optimize_model (requires a dummy model)
        class DummyModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.linear = torch.nn.Linear(10, 1)

        model = DummyModel()
        optimized_model = optimize_model(model)
        if optimized_model is None:
            logger.error("Optimization self-test failed: optimize_model returned None.")
            return False

        # Test cleanup_memory
        cleanup_memory()

        logger.info("Optimization self-test passed.")
        return True
    except Exception as e:
        logger.error(f"Optimization self-test failed: {e}")
        return False
