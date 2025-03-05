"""
Configuration settings for Luna.

This module provides access to configuration settings,
with optional loading from environment variables.
"""

import os
from dotenv import load_dotenv
from domain.models.config import AppConfig, APIKeys, DebugLevel

# Load environment variables if .env file exists
if os.path.exists('.env'):
    load_dotenv()

def get_api_keys() -> APIKeys:
    """
    Get API keys from environment variables.
    
    Returns:
        APIKeys: API keys
    """
    return APIKeys(
        anthropic_api_key=os.getenv('ANTHROPIC_API_KEY', ''),
        openrouter_api_key=os.getenv('OPENROUTER_API_KEY', '')
    )

def get_app_config() -> AppConfig:
    """
    Get application configuration from environment variables.
    
    Returns:
        AppConfig: Application configuration
    """
    # Parse debug level from environment
    debug_level_str = os.getenv('DEBUG_LEVEL', 'none').lower()
    try:
        debug_level = DebugLevel(debug_level_str)
    except ValueError:
        debug_level = DebugLevel.NONE
    
    return AppConfig(
        default_model=os.getenv('DEFAULT_MODEL', 'claude-3-7-sonnet-latest'),
        chroma_db_path=os.getenv('CHROMA_DB_PATH', 'chroma_db'),
        show_inner_thoughts=os.getenv('SHOW_INNER_THOUGHTS', 'True').lower() == 'true',
        log_inner_thoughts=os.getenv('LOG_INNER_THOUGHTS', 'False').lower() == 'true',
        inner_thoughts_log_path=os.getenv('INNER_THOUGHTS_LOG_PATH', 'logs/luna_debug.log'),
        debug_level=debug_level
    )