import logging
import requests
import pandas as pd
import matplotlib.pyplot as plt


from osmanli_ai.core.types import ComponentMetadata

logger = logging.getLogger(__name__)


class MarketAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.example.com"  # Replace with actual API base URL

    def get_stock_data(self, symbol: str, interval: str = "1d") -> pd.DataFrame:
        """Fetch stock data for a given symbol and interval."""
        url = f"{self.base_url}/stock/{symbol}/{interval}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            logger.error(
                f"Failed to fetch stock data for {symbol}: {response.status_code}"
            )
            return pd.DataFrame()

        data = response.json()
        df = pd.DataFrame(data)
        df.set_index("date", inplace=True)
        df.index = pd.to_datetime(df.index)
        return df

    def analyze_trends(self, df: pd.DataFrame) -> str:
        """Analyze trends in the stock data."""
        if df.empty:
            return "No data available for analysis."

        # Simple trend analysis (e.g., moving average)
        df["ma"] = df["close"].rolling(window=20).mean()
        current_price = df["close"].iloc[-1]
        ma_price = df["ma"].iloc[-1]

        if current_price > ma_price:
            return "The stock is trending upward."
        else:
            return "The stock is trending downward."

    def plot_stock_data(self, df: pd.DataFrame, symbol: str):
        """Plot the stock data for visualization."""
        plt.figure(figsize=(10, 5))
        plt.plot(df.index, df["close"], label="Close Price")
        plt.plot(df.index, df["ma"], label="Moving Average")
        plt.title(f"{symbol} Stock Price")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.show()

    def get_metadata(self) -> ComponentMetadata:
        return ComponentMetadata(
            name="MarketAnalyzer",
            version="1.0.0",
            description="Analyzes real-time market data and provides insights.",
            component_type="SERVICE",
            capabilities=["stock_analysis", "trend_analysis", "visualization"],
        )


if __name__ == "__main__":
    # Example usage
    analyzer = MarketAnalyzer(api_key="your_api_key_here")
    df = analyzer.get_stock_data("AAPL")
    trend = analyzer.analyze_trends(df)
    print(trend)
    analyzer.plot_stock_data(df, "AAPL")
