import os
import json
import numpy as np
from pathlib import Path
import faiss
from sentence_transformers import SentenceTransformer

# Directory Paths
BASE_DIR = Path(__file__).resolve().parent
CHUNKS_FILE = BASE_DIR / "processed" / "rag" / "chunks.json"
INDEX_DIR = BASE_DIR / "artifacts" / "faiss_nutrition_index"
ALT_INDEX_DIR = BASE_DIR.parent / "ml_artifacts" / "faiss_nutrition_index"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

INDEX_PATH = INDEX_DIR / "index.faiss"
METADATA_PATH = INDEX_DIR / "metadata.json"
CONFIG_PATH = INDEX_DIR / "config.json"


def build_faiss_index():
    """
    Build FAISS IndexFlatIP (Cosine Similarity) from processed NIDDK nutrition chunks.
    Does NOT train the LLM; embeds authoritative text chunks using SentenceTransformers.
    """
    print("=" * 75)
    print(f"[NutriTwin Phase 9] Building FAISS Vector Index using {MODEL_NAME}...")
    print("=" * 75)

    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(f"Processed RAG chunks missing at: {CHUNKS_FILE}")

    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    print("1. Loading RAG text chunks from processed JSON...")
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    num_chunks = len(chunks)
    print(f"   -> Loaded {num_chunks} authoritative NIDDK nutrition text chunks.")

    print(f"2. Loading Embedding Model: {MODEL_NAME}...")
    encoder = SentenceTransformer(MODEL_NAME)

    texts = [c["text"] for c in chunks]
    print(f"3. Generating 384-dim dense embeddings for {num_chunks} chunks...")
    embeddings = encoder.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    embeddings = embeddings.astype(np.float32)

    # Normalize vectors for Inner Product = Cosine Similarity
    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]
    print(f"4. Initializing FAISS IndexFlatIP (dimension={dimension})...")
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    print(f"   -> Total vectors indexed: {index.ntotal}")

    # Save artifacts
    print("5. Saving index and metadata artifacts...")
    faiss.write_index(index, str(INDEX_PATH))

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    config_data = {
        "model_name": MODEL_NAME,
        "embedding_dimension": dimension,
        "total_vectors": index.ntotal,
        "metric": "cosine",
        "index_type": "IndexFlatIP",
        "metadata_fields": list(chunks[0].keys()) if chunks else []
    }

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)

    if ALT_INDEX_DIR.exists():
        ALT_INDEX_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(ALT_INDEX_DIR / "index.faiss"))
        with open(ALT_INDEX_DIR / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"   -> Saved FAISS index: {INDEX_PATH}")
    print(f"   -> Saved metadata: {METADATA_PATH}")

    # 6. Test Semantic Retrieval on Representative Queries
    print("\n" + "=" * 75)
    print("SEMANTIC RETRIEVAL TEST RESULTS (REPRESENTATIVE NUTRITION QUERIES)")
    print("=" * 75)

    test_queries = [
        "What is the recommended dietary intake for managing diabetes?",
        "How does high sodium affect blood pressure and hypertension?",
        "What dietary changes help protect kidney function in chronic kidney disease?",
        "What are healthy eating patterns and dietary guidelines?"
    ]

    for q_idx, query in enumerate(test_queries, 1):
        q_emb = encoder.encode([query], convert_to_numpy=True).astype(np.float32)
        faiss.normalize_L2(q_emb)

        scores, indices = index.search(q_emb, k=3)
        top_scores = scores[0]
        top_indices = indices[0]

        print(f"\nQuery {q_idx}: \"{query}\"")
        print("-" * 75)

        for rank, (score, idx) in enumerate(zip(top_scores, top_indices), 1):
            chunk = chunks[idx]
            print(f" Rank {rank} [Similarity Score: {score:.4f}] | Doc: '{chunk['title']}' ({chunk['source']})")
            print(f" Source URL: {chunk['source_url']}")
            print(f" Text Snippet: {chunk['text'][:140]}...\n")

    print("=" * 75)
    return index, chunks


if __name__ == "__main__":
    build_faiss_index()
