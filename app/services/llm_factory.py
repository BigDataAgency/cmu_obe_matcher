from app.config import get_settings
from app.services.openai_service import OpenAIService
from app.services.gemini_service import GeminiService

def get_llm_service():
    """Factory function to return the configured LLM service."""
    settings = get_settings()
    provider = settings.llm_provider.lower()
    
    if provider == "gemini":
        return GeminiService()
    elif provider == "openai":
        return OpenAIService()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Use 'openai' or 'gemini'.")
