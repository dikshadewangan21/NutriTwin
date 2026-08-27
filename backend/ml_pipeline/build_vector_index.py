import os
import json
import numpy as np
from pathlib import Path
import faiss
from sentence_transformers import SentenceTransformer

# Path configuration
BASE_DIR = Path(__file__).resolve().parent
CHUNKS_FILE = BASE_DIR / "processed" / "rag" / "chunks.json"
ARTIFACTS_DIR = BASE_DIR / "artifacts" / "faiss_nutrition_index"
INDEX_FILE = ARTIFACTS_DIR / "index.faiss"
METADATA_FILE = ARTIFACTS_DIR / "metadata.json"
CONFIG_FILE = ARTIFACTS_DIR / "config.json"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def build_vector_index():
    """
    Loads preprocessed document chunks, generates embeddings using SentenceTransformer,
    builds a FAISS vector index, and persists the index & metadata to disk.
    """
    print("=" * 70)
    print("PHASE 9 — STEP 2: BUILD RAG VECTOR SEARCH INDEX")
    print("=" * 70)

    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(f"Chunks file missing at: {CHUNKS_FILE}. Please run preprocess_rag.py first.")

    # 1. Load chunks.json
    print(f"\n1. Loading chunks from: {CHUNKS_FILE}")
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    
    print(f"   -> Loaded {len(chunks)} chunks.")

    # Validate metadata schema
    required_keys = ["chunk_id", "source", "source_url", "title", "condition", "category", "original_file", "text"]
    for idx, c in enumerate(chunks):
        for k in required_keys:
            if k not in c:
                raise KeyError(f"Chunk at index {idx} missing metadata key '{k}'")

    # 2. Convert each chunk into an embedding using Sentence Transformers
    print(f"\n2. Initializing Sentence Transformer model: '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME)
    
    texts = [chunk["text"] for chunk in chunks]
    print(f"   -> Generating embeddings for {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    embeddings = embeddings.astype(np.float32)

    # Normalize vectors to unit length (L2 norm) for exact Cosine Similarity
    faiss.normalize_L2(embeddings)
    dimension = embeddings.shape[1]
    print(f"   -> Embedding matrix shape: {embeddings.shape} (Dimension: {dimension})")

    # 3. Build FAISS index for vector similarity search
    print(f"\n3. Building FAISS index (IndexFlatIP for Cosine Similarity)...")
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    print(f"   -> FAISS index built with {index.ntotal} vectors.")

    # 4 & 5. Save FAISS index and metadata
    print(f"\n4. Saving FAISS index & metadata to: {ARTIFACTS_DIR}")
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(INDEX_FILE))
    
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    config = {
        "model_name": MODEL_NAME,
        "embedding_dimension": dimension,
        "total_vectors": index.ntotal,
        "metric": "cosine",
        "index_type": "IndexFlatIP",
        "metadata_fields": required_keys
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"   - Index file   : {INDEX_FILE.name} ({INDEX_FILE.stat().st_size} bytes)")
    print(f"   - Metadata file: {METADATA_FILE.name} ({METADATA_FILE.stat().st_size} bytes)")
    print(f"   - Config file  : {CONFIG_FILE.name}")
    
    print("\n" + "=" * 70)
    print("VECTOR INDEX BUILD COMPLETE")
    print("=" * 70)
    
    return model, index, chunks

def test_rag_retrieval(model=None, index=None, chunks=None):
    """
    Tests the FAISS vector search index by querying 5 sample nutrition & health questions
    and displaying the top 3 retrieved chunks with full source metadata.
    """
    if model is None or index is None or chunks is None:
        print("\nLoading vector index from disk for testing...")
        model = SentenceTransformer(MODEL_NAME)
        index = faiss.read_index(str(INDEX_FILE))
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            chunks = json.load(f)

    sample_questions = [
        "What foods should I eat or avoid if I have diabetes?",
        "How can I protect my kidneys from damage if I have high blood pressure?",
        "What are the recommended dietary guidelines for managing chronic kidney disease?",
        "How many hours of sleep should I get to keep my body and kidneys healthy?",
        "What over-the-counter pain relievers or medicines can harm the kidneys?"
    ]

    print("\n" + "=" * 80)
    print("TESTING RETRIEVAL SYSTEM WITH 5 SAMPLE NUTRITION & HEALTH QUESTIONS")
    print("=" * 80)

    for q_idx, query in enumerate(sample_questions, 1):
        print(f"\n[QUESTION {q_idx}]: \"{query}\"")
        print("=" * 80)

        query_vec = model.encode([query], convert_to_numpy=True).astype(np.float32)
        faiss.normalize_L2(query_vec)

        top_k = 3
        scores, indices = index.search(query_vec, top_k)

        for rank, (score, chunk_idx) in enumerate(zip(scores[0], indices[0]), 1):
            chunk = chunks[chunk_idx]
            text_snippet = chunk['text']
            if len(text_snippet) > 200:
                text_snippet = text_snippet[:200] + "..."

            print(f"  Result #{rank} | Cosine Similarity Score: {score:.4f}")
            print(f"   - Chunk ID    : {chunk['chunk_id']}")
            print(f"   - Title       : {chunk['title']}")
            print(f"   - Condition   : {chunk['condition']}")
            print(f"   - Category    : {chunk['category']}")
            print(f"   - Source      : {chunk['source']}")
            print(f"   - Source URL  : {chunk['source_url']}")
            print(f"   - File        : {chunk['original_file']}")
            print(f"   - Text        : {text_snippet}\n")

if __name__ == "__main__":
    model, index, chunks = build_vector_index()
    test_rag_retrieval(model, index, chunks)
