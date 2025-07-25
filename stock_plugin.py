# osmanli_ai/plugins/finance/stock_plugin.py

import logging
import os
import re
import time
from typing import Optional, Dict, Any

import requests
from osmanli_ai.plugins.base import BasePlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class Plugin(BasePlugin):
    """
    Financial plugin using Alpha Vantage API for real-time stock data.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = "https://www.alphavantage.co/query"
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY") or config.get(
            "plugins", {}
        ).get("StockMonitorPlugin", {}).get("ALPHA_VANTAGE_API_KEY", "MYRRHOYIVSG9V0NV")
        self.rate_limit_delay = 15  # seconds between requests (free tier limit)
        self.last_request_time = 0
        logger.info("Alpha Vantage StockMonitor initialized")

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="StockMonitorPlugin",
            version="0.4.0",
            author="Osmanli AI",
            description="Fetches real-time stock prices, company overviews, and market news using Alpha Vantage API",
            plugin_type=PluginType.FINANCE,
            capabilities=["stock_price", "company_overview", "market_news"],
            dependencies=["requests"],
        )

    def _enforce_rate_limit(self):
        """Enforce API rate limits (5 requests/minute for free tier)"""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def _get_stock_price(self, symbol: str) -> str:
        """Get current stock price with additional market data"""
        self._enforce_rate_limit()

        params = {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": self.api_key}

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "Global Quote" in data and data["Global Quote"]:
                quote = data["Global Quote"]
                return (
                    f"{symbol.upper()}:\n"
                    f"• Price: ${quote.get('05. price', 'N/A')}\n"
                    f"• Change: {quote.get('09. change', 'N/A')} ({quote.get('10. change percent', 'N/A')})\n"
                    f"• Day's Range: {quote.get('03. low', 'N/A')}-{quote.get('04. high', 'N/A')}\n"
                    f"• Volume: {quote.get('06. volume', 'N/A')}"
                )
            elif "Note" in data:
                return (
                    "API rate limit reached. Please wait before making another request."
                )
            else:
                return f"No data available for {symbol}. Check the symbol is correct."

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            return f"Failed to fetch stock data: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return f"An error occurred: {str(e)}"

    def _get_company_overview(self, symbol: str) -> str:
        """Get comprehensive company overview"""
        self._enforce_rate_limit()

        params = {"function": "OVERVIEW", "symbol": symbol, "apikey": self.api_key}

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data:
                return f"No overview data available for {symbol}"

            return (
                f"Company: {data.get('Name', 'N/A')} ({symbol.upper()})\n"
                f"Sector: {data.get('Sector', 'N/A')}\n"
                f"Industry: {data.get('Industry', 'N/A')}\n"
                f"Market Cap: ${data.get('MarketCapitalization', 'N/A')}\n"
                f"PE Ratio: {data.get('PERatio', 'N/A')}\n"
                f"52 Week Range: {data.get('52WeekLow', 'N/A')}-{data.get('52WeekHigh', 'N/A')}\n"
                f"Dividend Yield: {data.get('DividendYield', 'N/A')}\n"
                f"Description: {data.get('Description', 'No description available.')[:300]}..."
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            return f"Failed to fetch company data: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return f"An error occurred: {str(e)}"

    def _get_market_overview(self) -> str:
        """Get a brief overview of the current market conditions."""
        # First, try to get news sentiment
        news = self._get_news_sentiment()
        if "Could not retrieve" not in news:
            return news

        # If news fails, fall back to top gainers and losers
        logger.warning("News sentiment API failed, falling back to top gainers/losers.")
        return self._get_top_gainers_losers()

    def _get_news_sentiment(self) -> str:
        """Fetches news sentiment from Alpha Vantage."""
        self._enforce_rate_limit()
        params = {
            "function": "NEWS_SENTIMENT",
            "topics": "earnings,ipo,mergers_and_acquisitions,financial_markets,economy_fiscal,economy_monetary,economy_macro,energy,technology",
            "apikey": self.api_key,
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            if "feed" in data and data["feed"]:
                articles = data["feed"][:5]
                overview = "Market News:\n"
                for article in articles:
                    overview += f"• {article['title']} ({article['source']})\n"
                return overview
            else:
                logger.warning("No news sentiment data available.")
                return "Could not retrieve market news at this time."
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching market news: {e}")
            return "Could not retrieve market news due to a network error."
        except Exception as e:
            logger.error(f"Unexpected error fetching market news: {e}")
            return "An unexpected error occurred while fetching market news."

    def _get_top_gainers_losers(self) -> str:
        """Fetches top gainers and losers from Alpha Vantage with colorized output."""
        self._enforce_rate_limit()
        params = {"function": "TOP_GAINERS_LOSERS", "apikey": self.api_key}
        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            if "top_gainers" in data and "top_losers" in data:
                gainers = data["top_gainers"][:5]
                losers = data["top_losers"][:5]
                overview = "<b>Top 5 Gainers:</b>\n"
                for gainer in gainers:
                    overview += f"• {gainer['ticker']} <span style='color:green;'> (+{gainer['change_percentage']})</span>\n"
                overview += "\n<b>Top 5 Losers:</b>\n"
                for loser in losers:
                    overview += f"• {loser['ticker']} <span style='color:red;'> ({loser['change_percentage']})</span>\n"
                return overview
            else:
                logger.warning("No top gainers/losers data available.")
                return "Could not retrieve market overview at this time."
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching top gainers/losers: {e}")
            return "Could not retrieve market overview due to a network error."
        except Exception as e:
            logger.error(f"Unexpected error fetching top gainers/losers: {e}")
            return "An unexpected error occurred while fetching market overview."

    def process(self, query: str, context: dict = None) -> Optional[str]:
        """Process financial queries with improved logic."""
        query_lower = query.lower().strip()

        # 1. Handle specific, non-symbol commands first
        if query_lower in ["stockmarket", "market overview"]:
            return self._get_market_overview()

        if query_lower in ["stocks", "stockmonitor", "stock monitor"]:
            return self.get_help()

        # 2. Handle queries like "price of AAPL" or "overview of GOOG"
        match = re.search(
            r"^(price|quote|value|overview|info)\s+(?:of|for)?\s*([A-Z]{1,5})\s*$",
            query_lower,
        )
        if match:
            keyword = match.group(1)
            symbol = match.group(2).upper()
            if keyword in ["price", "quote", "value"]:
                return self._get_stock_price(symbol)
            else:  # overview, info
                return self._get_company_overview(symbol)

        # 3. Handle queries that are just the symbol, e.g., "AAPL"
        if re.fullmatch(r"[A-Z]{1,5}", query_lower.upper()):
            symbol = query_lower.upper()
            price_info = self._get_stock_price(symbol)
            overview_info = self._get_company_overview(symbol)
            if (
                "No data available" in price_info
                and "No overview data available" in overview_info
            ):
                return f"No data available for {symbol}. Check the symbol is correct."
            return f"{price_info}\n\n{overview_info}"

        # 4. If no match, return None to allow other plugins to process the query.
        return None

    def get_help(self) -> str:
        """Provides helpful instructions on how to use the plugin."""
        return (
            "StockMonitor Plugin: To get information about a stock, please provide a stock symbol.\n"
            "Examples:\n"
            '• To get a full overview: "AAPL"\n'
            '• To get the price: "price of AAPL"\n'
            '• To get company details: "overview of AAPL"\n'
            '• To get a market overview: "stockmarket"'
        )
