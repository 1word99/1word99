# osmanli_ai/plugins/web/search.py
import logging
import os

import requests  # For making web requests

from osmanli_ai.plugins.base import BasePlugin  # Inherit from BasePlugin
from osmanli_ai.plugins.base import PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class Plugin(BasePlugin):  # Inherit from BasePlugin
    def __init__(self, config: dict):
        super().__init__(config)
        self.search_endpoint = "https://www.searchapi.io/api/v1/search"
        self.api_key = os.getenv("SEARCHAPI_API_KEY") or config.get("plugins", {}).get(
            "WebSearchPlugin", {}
        ).get("SEARCHAPI_API_KEY")
        if not self.api_key:
            logger.warning(
                "SEARCHAPI_API_KEY not found in config for WebSearchPlugin. Web search may fail."
            )
        logger.info("WebSearch plugin initialized.")

    @classmethod
    def get_metadata(cls) -> PluginMetadata:
        return PluginMetadata(
            name="WebSearchPlugin",
            version="0.1.0",
            author="Osmanli AI",
            description="Provides web search capabilities.",
            plugin_type=PluginType.KNOWLEDGE,
            capabilities=["web_search", "information_retrieval"],
            dependencies=[],
        )

    def process(self, query: str, context: dict = None) -> str:
        logger.info(f"Processing query: {query}")

        if not self.api_key:
            return "Web search failed: SEARCHAPI_API_KEY is not configured."

        try:
            params = {"engine": "duckduckgo", "q": query, "api_key": self.api_key}
            request_url = (
                requests.Request("GET", self.search_endpoint, params=params)
                .prepare()
                .url
            )
            logger.debug(
                f"WebSearch: Requesting URL: {request_url.replace(self.api_key, '[MASKED_API_KEY]')}"
            )
            response = requests.get(self.search_endpoint, params=params)
            response.raise_for_status()  # Raise an exception for HTTP errors
            search_results = response.json()
            if (
                "organic_results" in search_results
                and search_results["organic_results"]
            ):
                return f"Web Search results for '{query}': {search_results['organic_results'][0]['snippet']}"
            else:
                return f"No search results found for '{query}'."

        except requests.exceptions.RequestException as e:
            logger.error(f"Error during web search for '{query}': {e}")
            return f"An error occurred while performing a web search for '{query}'. Please try again later."
        except Exception as e:
            logger.error(f"Unexpected error in WebSearch plugin: {e}", exc_info=True)
            return "An unexpected error occurred during web search. Details logged."
