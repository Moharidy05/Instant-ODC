class RagError(Exception):
    """Base exception for the Diabetes Food Safety RAG system."""


class ConfigurationError(RagError):
    """Raised when required configuration is missing or invalid."""


class RetrievalError(RagError):
    """Raised when retrieval fails."""


class ModelFallbackExhausted(RagError):
    """Raised when all configured model/key combinations fail."""


class InsufficientEvidenceError(RagError):
    """Raised when retrieved evidence is below the configured threshold."""
