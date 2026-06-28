"""Application configuration and metadata."""

APP_NAME = "Creator Atlas"
APP_TAGLINE = "Explore the creator landscape through AI-powered embeddings"
APP_VERSION = "0.1.0"
APP_REPO_URL = "https://github.com/amberverma16/creator-atlas"

# Placeholder map settings (used once visualization is implemented)
MAP_HEIGHT = 620
NEIGHBOR_COUNT = 10

# Embedding model (sentence-transformers)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# UMAP (map layout)
UMAP_N_NEIGHBORS = 15
UMAP_MIN_DIST = 0.1
UMAP_METRIC = "cosine"
UMAP_RANDOM_STATE = 42
