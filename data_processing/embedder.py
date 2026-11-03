# Dependencies: requests, fastembed, qdrant-client. No GPU is required.
# Set the paths below and the OPENROUTER_API_KEY environment variable.

import json
import math
import os
import shutil
import time
from pathlib import Path

import requests
from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models


CHUNKS_FILE = Path("")  # insert summarized chunks file path
QDRANT_PATH = Path("")  # insert a new output folder path
ARCHIVE_PATH = ""  # optional ZIP output path, without .zip
BATCH_SIZE = 99
EMBEDDING_DIM = 3072
DOCUMENT_PREFIX = "title: none | text: "
# Retrieval queries must use: task: search result | query: {question}


def embed_dense(summaries, session):
    inputs = [DOCUMENT_PREFIX + summary for summary in summaries]
    # Conservative byte guard, not a token limit; never truncate summaries.
    if any(len(text.encode("utf-8")) > 8000 for text in inputs):
        raise ValueError("An embedding input exceeds the 8000-byte guard.")

    for attempt in range(3):
        response = session.post(
            "https://openrouter.ai/api/v1/embeddings",
            json={
                "model": "google/gemini-embedding-2",
                "input": inputs,
                "dimensions": EMBEDDING_DIM,
                "encoding_format": "float",
                "provider": {"only": ["google-ai-studio"], "allow_fallbacks": False},
            },
            timeout=(15, 180),
        )
        if response.status_code not in (429, 500, 502, 503, 504):
            break
        if attempt < 2:
            time.sleep(2 ** (attempt + 1))

    response.raise_for_status()
    items = sorted(response.json()["data"], key=lambda item: item["index"])
    if [item["index"] for item in items] != list(range(len(summaries))):
        raise ValueError("Missing or duplicate embedding vectors.")
    vectors = [item["embedding"] for item in items]
    if any(len(vector) != EMBEDDING_DIM or not all(map(math.isfinite, vector)) for vector in vectors):
        raise ValueError("Embedding vectors have invalid dimensions or values.")
    return vectors


if QDRANT_PATH.exists():
    raise FileExistsError("Choose a new QDRANT_PATH; existing folders are never overwritten.")

chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
if not chunks or any(not isinstance(chunk.get("summary"), str) or not chunk["summary"].strip() for chunk in chunks):
    raise ValueError("Every chunk must have a nonempty summary before embedding.")
api_key = os.environ["OPENROUTER_API_KEY"]
sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

client = QdrantClient(path=str(QDRANT_PATH))
try:
    client.create_collection(
        collection_name="sec_filings",
        vectors_config={"dense": models.VectorParams(size=EMBEDDING_DIM, distance=models.Distance.COSINE)},
        sparse_vectors_config={"sparse": models.SparseVectorParams(index=models.SparseIndexParams(on_disk=False))},
    )
    with requests.Session() as session:
        session.headers.update({"Authorization": f"Bearer {api_key}"})
        # Embed and save one batch at a time. Failed runs do not resume automatically.
        for start in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[start:start + BATCH_SIZE]
            summaries = [chunk["summary"] for chunk in batch]
            dense_vectors = embed_dense(summaries, session)
            sparse_vectors = list(sparse_model.embed(summaries, batch_size=256))
            points = [
                models.PointStruct(
                    id=start + offset,
                    vector={
                        "dense": dense,
                        "sparse": models.SparseVector(
                            indices=sparse.indices.tolist(),
                            values=sparse.values.tolist(),
                        ),
                    },
                    payload={
                        "page_content": chunk["summary"],
                        "metadata": {key: value for key, value in chunk.items() if key != "summary"},
                    },
                )
                for offset, (chunk, dense, sparse) in enumerate(
                    zip(batch, dense_vectors, sparse_vectors, strict=True)
                )
            ]
            client.upsert(collection_name="sec_filings", points=points, wait=True)
            print(f"Saved {start + len(batch)}/{len(chunks)} chunks.")
finally:
    client.close()

if ARCHIVE_PATH:
    print("Saved:", shutil.make_archive(ARCHIVE_PATH, "zip", str(QDRANT_PATH)))
