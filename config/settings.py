"""
Configuration settings for Luna.

This module provides access to configuration settings,
with optional loading from environment variables.
"""

import os

from dotenv import load_dotenv

from domain.models.config import APIKeys, AppConfig

# Load environment variables if .env file exists
if os.path.exists(".env"):
    load_dotenv()


def get_api_keys() -> APIKeys:
    """
    Get API keys from environment variables.

    Returns:
        APIKeys: API keys
    """
    return APIKeys(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
    )


def get_app_config() -> AppConfig:
    """
    Get application configuration from environment variables.

    Returns:
        AppConfig: Application configuration
    """
    return AppConfig(
        default_model=os.getenv("DEFAULT_MODEL", "claude-3-7-sonnet-latest"),
        elasticsearch_url=os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"),
        show_agent_thinking=os.getenv("SHOW_AGENT_THINKING", "True").lower() == "true",
        logs_path=os.getenv("LOGS_PATH", "logs"),
    )
