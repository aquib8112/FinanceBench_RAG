from fastembed import SparseTextEmbedding
import os

# This path matches the default Linux cache location
os.environ["FASTEMBED_CACHE_PATH"] = "/app/fastembed_cache"

def download():
    print("Downloading BM25 model...")
    # This triggers the download
    SparseTextEmbedding(model_name="Qdrant/bm25", cache_dir="/app/fastembed_cache")
    print("Download complete.")

if __name__ == "__main__":
    download()