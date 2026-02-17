from app.config import get_settings
from app.services.openai_service import OpenAIService

def get_llm_service():
    """Factory function to return the configured LLM service."""
    _ = get_settings()
    return OpenAIService()
