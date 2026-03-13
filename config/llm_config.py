"""LLM Configuration for AI Engine"""
import os
from typing import Literal
from dotenv import load_dotenv

load_dotenv()

class LLMConfig:
    """Configuration for Language Model"""

    # OpenAI Settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Using mini for cost efficiency
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))  # Deterministic for security queries
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))

    # Query Processing Settings
    QUERY_INTENT_THRESHOLD = 0.7  # Confidence threshold for intent classification
    MAX_QUERY_LENGTH = 500  # Maximum characters in user query

    # Elasticsearch Query Generation Settings
    MAX_RESULTS = 100  # Maximum results to return from Elasticsearch
    DEFAULT_TIME_RANGE = "24h"  # Default time range for queries

    # Supported query intents
    QUERY_INTENTS = [
        "search_logs",           # Search security logs
        "investigate_incident",  # Investigate specific incident
        "threat_intel_lookup",   # Look up threat intelligence
        "generate_report",       # Generate security report
        "analyze_behavior",      # Analyze behavioral patterns
        "hunt_threats"           # Proactive threat hunting
    ]

    @classmethod
    def validate(cls) -> bool:
        """Validate that required configuration is present"""
        if not cls.OPENAI_API_KEY:
            return False
        return True

    @classmethod
    def get_model_name(cls) -> str:
        """Get the current model name"""
        return cls.OPENAI_MODEL
