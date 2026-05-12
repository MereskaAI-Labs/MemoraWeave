from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings

def build_embeddings():
    """Initialize and return GoogleGenerativeAIEmbeddings"""
    api_key = settings.google_api_key or settings.gemini_api_key
    
    if not api_key:
        raise RuntimeError(
            "API key Gemini belum terbaca. Isi GOOGLE_API_KEY atau GEMINI_API_KEY di .env"
        )
        
    return GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=api_key,
        output_dimensionality=settings.embedding_dimensions
    )