"""
Application configuration management.
Loads settings from environment variables and .env file with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application configuration settings."""
    
    TOGETHER_API_KEY: str = os.getenv("TOGETHER_API_KEY", "")
    TOGETHER_BASE_URL: str = os.getenv("TOGETHER_BASE_URL", "https://api.together.xyz/v1")
    TOGETHER_MODEL: str = os.getenv("TOGETHER_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo")
    TOGETHER_TIMEOUT: float = float(os.getenv("TOGETHER_TIMEOUT", "60.0"))
    
    MEMORY_FILE: str = os.getenv("MEMORY_FILE", "agent_memory.json")
    
    LOG_DIR: str = os.getenv("LOG_DIR", "logs")
    LOG_CONSOLE_LEVEL: str = os.getenv("LOG_CONSOLE_LEVEL", "INFO")
    LOG_FILE_LEVEL: str = os.getenv("LOG_FILE_LEVEL", "DEBUG")
    
    AGENT_MAX_ITERATIONS: int = int(os.getenv("AGENT_MAX_ITERATIONS", "5"))
    AGENT_MAX_TOKENS: int = int(os.getenv("AGENT_MAX_TOKENS", "2000"))
    AGENT_TEMPERATURE: float = float(os.getenv("AGENT_TEMPERATURE", "0.7"))
    
    EVALUATOR_TIMEOUT: float = float(os.getenv("EVALUATOR_TIMEOUT", "30.0"))
    EVALUATOR_MAX_TOKENS: int = int(os.getenv("EVALUATOR_MAX_TOKENS", "1000"))
    EVALUATOR_TEMPERATURE: float = float(os.getenv("EVALUATOR_TEMPERATURE", "0.3"))
    
    LEARNING_WINDOW_SIZE: int = int(os.getenv("LEARNING_WINDOW_SIZE", "10"))
    LEARNING_THRESHOLD: int = int(os.getenv("LEARNING_THRESHOLD", "2"))


settings = Settings()

