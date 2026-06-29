"""Application configuration and metadata."""

APP_NAME = "Creator Atlas"
APP_TAGLINE = "Explore the creator landscape through AI-powered embeddings"
APP_VERSION = "0.1.0"
APP_REPO_URL = "https://github.com/amberverma16/creator-atlas"

# Placeholder map settings (used once visualization is implemented)
MAP_HEIGHT = 850
NEIGHBOR_COUNT = 10

# Map level-of-detail (zoom factor thresholds)
LOD_DOTS_ZOOM = 1.8
LOD_LABELS_ZOOM = 3.5
MAX_REGION_LABELS = 8
ZOOM_STEP = 1.35

# Embedding model (sentence-transformers)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# UMAP (map layout)
UMAP_N_NEIGHBORS = 15
UMAP_MIN_DIST = 0.1
UMAP_METRIC = "cosine"
UMAP_RANDOM_STATE = 42
