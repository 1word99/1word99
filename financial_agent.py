from typing import Any, Dict, Optional

from loguru import logger

from osmanli_ai.core.agent import BaseAgent
from osmanli_ai.core.enums import ComponentType
from osmanli_ai.core.stock_monitor import (
    StockMonitor,
)  # Assuming StockMonitor is available
from osmanli_ai.core.types import ComponentMetadata


class FinancialAgent(BaseAgent):
    """
    A specialized agent for handling financial queries and stock monitoring.
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.stock_monitor = StockMonitor(config)  # Initialize StockMonitor
        logger.info("FinancialAgent initialized.")

    @classmethod
    def get_metadata(cls) -> ComponentMetadata:
        return ComponentMetadata(
            name="FinancialAgent",
            version="0.1.0",
            description="Handles financial queries, stock prices, and market monitoring.",
            component_type=ComponentType.AGENT,
            author="Osmanli AI",
            capabilities=["stock_price", "stock_monitoring", "financial_news"],
        )

    def can_handle_query(self, query: str) -> bool:
        """
        Determines if the FinancialAgent can handle a given natural language query.
        """
        query_lower = query.lower()
        return any(
            keyword in query_lower
            for keyword in [
                "stock",
                "price",
                "market",
                "finance",
                "financial",
                "monitor",
            ]
        )

    async def process_task(
        self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processes a financial-related task.

        Args:
            task (Dict[str, Any]): The task to process. Expected to have 'type' and 'payload'.
            context (Optional[Dict[str, Any]]): Additional context for the task.

        Returns:
            Dict[str, Any]: The result of the financial task.
        """
        task_type = task.get("type")
        payload = task.get("payload", {})

        if task_type == "get_stock_price":
            symbol = payload.get("symbol")
            if symbol:
                price = self.stock_monitor.get_current_price(symbol)
                if price is not None:
                    return {
                        "status": "success",
                        "result": f"The current price of {symbol} is {price:.2f}.",
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Could not retrieve price for {symbol}.",
                    }
            else:
                return {"status": "error", "message": "No stock symbol provided."}
        elif task_type == "monitor_stock":
            symbol = payload.get("symbol")
            threshold = payload.get("threshold", 0.05)  # Default 5%
            if symbol:
                # This would ideally trigger continuous monitoring in the background
                # For now, just acknowledge the request
                return {
                    "status": "success",
                    "result": f"Monitoring for {symbol} with a threshold of {threshold*100:.0f}% has been initiated. (Placeholder)",
                }
            else:
                return {
                    "status": "error",
                    "message": "No stock symbol provided for monitoring.",
                }
        else:
            return {
                "status": "error",
                "message": f"Unknown financial task type: {task_type}",
            }

    def self_test(self) -> bool:
        """
        Performs a self-test of the FinancialAgent component.
        """
        logger.info("Running self-test for FinancialAgent...")
        try:
            # Test metadata
            metadata = self.get_metadata()
            if metadata.name != "FinancialAgent":
                logger.error("FinancialAgent self-test failed: Metadata name mismatch.")
                return False

            # Test can_handle_query
            if not self.can_handle_query("what is the stock price of AAPL"):
                logger.error(
                    "FinancialAgent self-test failed: can_handle_query failed."
                )
                return False

            # Test process_task (get_stock_price) - requires actual network call, so mock or skip in CI
            # For now, we'll just test the call structure, not live data.
            # Mock the get_current_price method of StockMonitor
            original_get_price = self.stock_monitor.get_current_price
            self.stock_monitor.get_current_price = lambda symbol: (
                150.00 if symbol == "TEST" else None
            )

            task_price = {"type": "get_stock_price", "payload": {"symbol": "TEST"}}
            result_price = self.process_task(task_price)
            if (
                result_price["status"] != "success"
                or "150.00" not in result_price["result"]
            ):
                logger.error(
                    "FinancialAgent self-test failed: get_stock_price task failed."
                )
                return False

            # Restore original method
            self.stock_monitor.get_current_price = original_get_price

            logger.info("FinancialAgent self-test passed.")
            return True
        except Exception as e:
            logger.error(f"FinancialAgent self-test failed: {e}", exc_info=True)
            return False
