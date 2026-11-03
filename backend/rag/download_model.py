import os
from pathlib import Path

from fastembed import SparseTextEmbedding


def download():
    cache_dir = os.getenv(
        "FASTEMBED_CACHE_PATH",
        str(Path(__file__).resolve().parents[1] / "data" / "fastembed_cache"),
    )
    print("Downloading BM25 model...")
    SparseTextEmbedding(model_name="Qdrant/bm25", cache_dir=cache_dir)
    print("Download complete.")


if __name__ == "__main__":
    download()
