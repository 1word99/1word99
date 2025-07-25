import inspect
import logging
from typing import AsyncGenerator, Callable

logger = logging.getLogger(__name__)


class Streamer:
    """
    A utility class for handling various types of data streaming.
    Can be extended for real-time audio, video, or text streams.
    """

    def __init__(self):
        logger.info("Streamer initialized.")

    async def stream_data(
        self, source: AsyncGenerator, process_func: Callable = None
    ) -> AsyncGenerator:
        """
        Streams data from an asynchronous generator, optionally processing each chunk.

        Args:
            source: An asynchronous generator yielding data chunks.
            process_func: An optional callable to process each data chunk.

        Yields:
            Processed or raw data chunks.
        """
        logger.debug("Starting data stream.")
        async for chunk in source:
            if process_func:
                processed_chunk = (
                    await process_func(chunk)
                    if inspect.iscoroutinefunction(process_func)
                    else process_func(chunk)
                )
                yield processed_chunk
            else:
                yield chunk
        logger.debug("Data stream finished.")

    def self_test(self) -> bool:
        """Performs a self-test of the Streamer component."""
        logger.info("Running self-test for Streamer...")
        try:

            async def dummy_source():
                yield "chunk1"
                yield "chunk2"

            async def dummy_process(chunk):
                return chunk.upper()

            async def run_test():
                stream_gen = self.stream_data(dummy_source(), dummy_process)
                results = [chunk async for chunk in stream_gen]
                return results == ["CHUNK1", "CHUNK2"]

            import asyncio

            if asyncio.run(run_test()):
                logger.info("Streamer self-test passed.")
                return True
            else:
                logger.error("Streamer self-test failed: Stream processing incorrect.")
                return False
        except Exception as e:
            logger.error(f"Streamer self-test failed: {e}")
            return False
