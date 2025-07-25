import logging
import time
from threading import Thread
from typing import Any
import yfinance as yf


logger = logging.getLogger(__name__)


class StockMonitor:
    def __init__(self, config: Any):
        self.config = config
        self.watched = {}
        self.thread = None
        self._running = False

    def start_monitoring(self, symbol, callback):
        """Start monitoring a stock"""
        self.watched[symbol] = callback
        if not self.thread or not self.thread.is_alive():
            self._running = True
            self.thread = Thread(target=self._monitor, daemon=True)
            self.thread.start()
            logger.info(f"Started monitoring thread for stock: {symbol}")

    def start(self):
        """Starts the stock monitoring with default values from config."""
        default_symbol = self.config.get("DEFAULT_STOCK_SYMBOL", "AAPL")
        _ = self.config.get("DEFAULT_STOCK_THRESHOLD", 0.05)
        _ = self.config.get("DEFAULT_STOCK_INTERVAL", "1d")

        # You'll need to define a default callback or pass one from Assistant
        # For now, we'll use a dummy callback that just logs
        def default_alert_callback(symbol, data):
            logger.info(f"Default stock alert for {symbol}: {data}")

        self.start_monitoring(default_symbol, default_alert_callback)

    def stop(self):
        """Stop monitoring all stocks and terminate the thread."""
        self._running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)  # Give the thread some time to finish
            if self.thread.is_alive():
                logger.warning("StockMonitor thread did not terminate gracefully.")
        logger.info("StockMonitor stopped.")

    def _monitor(self):
        while self._running:
            for symbol, callback in list(
                self.watched.items()
            ):  # Iterate over a copy to allow modification
                try:
                    data = yf.Ticker(symbol).history(period="1d")
                    if data.empty:
                        logger.warning(
                            f"No data found for stock symbol: {symbol}. Skipping."
                        )
                        continue

                    if self._check_alert(data):
                        callback(symbol, data)  # Pass data to callback
                except Exception as e:
                    logger.error(f"Error monitoring stock {symbol}: {e}")
            time.sleep(60)  # Check every minute

    def _check_alert(self, data):
        # Implement your alert logic here
        return (data["Close"][-1] - data["Open"][0]) / data["Open"][0] < -0.05

    def self_test(self) -> bool:
        """Performs a self-test of the StockMonitor component.
        Returns True if the component is healthy, False otherwise.
        """
        logger.info("Running self-test for StockMonitor...")
        try:
            # Test yfinance import and basic data retrieval

            ticker = yf.Ticker("AAPL")
            data = ticker.history(period="1d")
            if data.empty:
                logger.error(
                    "StockMonitor self-test failed: Could not retrieve AAPL data."
                )
                return False

            # Test watch and stop methods (without actually starting a long-running thread)
            monitor = StockMonitor(self.config)  # Pass config to init
            test_callback_called = False

            def test_callback(symbol, data):
                nonlocal test_callback_called
                test_callback_called = True

            monitor.watch("MSFT", test_callback)
            monitor.stop()

            if monitor._running:
                logger.error(
                    "StockMonitor self-test failed: Monitor thread did not stop."
                )
                return False

            logger.info("StockMonitor self-test passed.")
            return True
        except Exception as e:
            logger.error(f"StockMonitor self-test failed: {e}")
            return False
