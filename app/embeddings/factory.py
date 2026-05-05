from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings

def build_embeddings():
    """Initialize and return GoogleGenerativeAIEmbeddings"""
    return GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        output_dimensionality=settings.embedding_dimensions
    )