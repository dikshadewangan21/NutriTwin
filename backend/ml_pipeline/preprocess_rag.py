import os
import re
import json
from pathlib import Path
import pypdf

# Directory paths
BASE_DIR = Path(__file__).resolve().parent
DATASET_RAG_DIR = BASE_DIR / "datasets" / "rag"
OUTPUT_DIR = BASE_DIR / "processed" / "rag"
OUTPUT_FILE = OUTPUT_DIR / "chunks.json"

TARGET_FOLDERS = ["diabetes", "kidney", "hypertension", "nutrition"]

CATEGORY_MAP = {
    "diabetes": "Diabetes Care & Management",
    "kidney": "Kidney Disease & Prevention",
    "hypertension": "Hypertension & Blood Pressure",
    "nutrition": "Diet & Nutrition Guidelines"
}

# Source URL mapping based on official NIDDK document paths
SOURCE_URL_MAP = {
    "Diabetes - NIDDK.pdf": "https://www.niddk.nih.gov/health-information/diabetes",
    "Healthy Living with Diabetes - NIDDK.pdf": "https://www.niddk.nih.gov/health-information/diabetes/overview/healthy-living-with-diabetes",
    "Kidney Disease - NIDDK.pdf": "https://www.niddk.nih.gov/health-information/kidney-disease",
    "Managing Chronic Kidney Disease - NIDDK.pdf": "https://www.niddk.nih.gov/health-information/kidney-disease/chronic-kidney-disease-ckd/managing",
    "Preventing Chronic Kidney Disease - NIDDK.pdf": "https://www.niddk.nih.gov/health-information/kidney-disease/chronic-kidney-disease-ckd/prevention",
    "Search - NIDDK.pdf": "https://www.niddk.nih.gov/search?s=all&q=blood+pressure",
    "Diet & Nutrition - NIDDK.pdf": "https://www.niddk.nih.gov/health-information/diet-nutrition"
}

def extract_doc_title(filename: str, first_page_text: str = "") -> str:
    """
    Extracts clean document title from filename or initial page header.
    """
    title = filename.replace(".pdf", "").replace(" - NIDDK", "").strip()
    if title.lower() == "search":
        title = "Blood Pressure & Health Information (NIDDK Search)"
    return title

def clean_text(raw_text: str) -> str:
    """
    Cleans web/navigation noise, header/footer timestamps, URLs, unicode icons, and formatting artifacts.
    """
    lines = raw_text.split('\n')
    cleaned_lines = []

    for line in lines:
        l = line.strip()
        if not l:
            continue
        
        # Filter web URLs
        if re.search(r'https?://\S+', l, re.IGNORECASE):
            continue
        
        # Filter print timestamps e.g. '26/08/2026, 01:05 Managing Chronic Kidney Disease - NIDDK'
        if re.search(r'^\d{2}/\d{2}/\d{4},\s*\d{2}:\d{2}', l):
            continue

        # Filter web search results navigation noise
        if re.search(r'^(Entire Site|Search Results|Show \d+ results per page|Search site\.\.\. Search|Results \d+ - \d+ of \d+)', l, re.IGNORECASE):
            continue
            
        if re.search(r'^(More .* Topics|More Research News|More Resources for .*)\ue000?', l, re.IGNORECASE):
            continue

        # Remove private unicode symbols (e.g. \ue000, \ue03a, \ue03b, \ue006)
        l = re.sub(r'[\ue000-\uefff]', '', l).strip()
        if not l:
            continue

        cleaned_lines.append(l)

    full_text = "\n".join(cleaned_lines)

    # Fix line-break hyphenation (e.g. "diabe-\ntes" -> "diabetes")
    full_text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', full_text)
    
    # Normalize paragraphs: split by multiple newlines
    paragraphs = [p.strip() for p in re.split(r'\n{2,}', full_text) if p.strip()]
    normalized_paragraphs = []
    for p in paragraphs:
        p_clean = re.sub(r'\s*\n\s*', ' ', p)
        p_clean = re.sub(r'[ \t]+', ' ', p_clean).strip()
        if len(p_clean) > 0:
            normalized_paragraphs.append(p_clean)

    return "\n\n".join(normalized_paragraphs)

def chunk_text(text: str, max_chunk_size: int = 600, overlap: int = 100) -> list[str]:
    """
    Splits text into small chunks with overlap, prioritizing paragraph and sentence boundaries.
    """
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if not current_chunk:
            current_chunk = para
        elif len(current_chunk) + len(para) + 2 <= max_chunk_size:
            current_chunk += "\n\n" + para
        else:
            chunks.append(current_chunk)
            
            # Create overlap
            if len(current_chunk) > overlap:
                overlap_text = current_chunk[-overlap:]
                space_idx = overlap_text.find(" ")
                if space_idx != -1:
                    overlap_text = overlap_text[space_idx + 1:]
                current_chunk = overlap_text + "\n\n" + para
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    # Secondary split for oversized chunks
    final_chunks = []
    for c in chunks:
        if len(c) <= max_chunk_size * 1.3:
            if len(c.strip()) >= 40:
                final_chunks.append(c.strip())
        else:
            sentences = re.split(r'(?<=[.!?])\s+', c)
            sub_chunk = ""
            for sent in sentences:
                if not sub_chunk:
                    sub_chunk = sent
                elif len(sub_chunk) + len(sent) + 1 <= max_chunk_size:
                    sub_chunk += " " + sent
                else:
                    if len(sub_chunk.strip()) >= 40:
                        final_chunks.append(sub_chunk.strip())
                    sub_chunk = sent
            if len(sub_chunk.strip()) >= 40:
                final_chunks.append(sub_chunk.strip())

    return final_chunks

def run_preprocessing_pipeline():
    """
    Executes Phase 9 RAG Preprocessing.
    """
    print("=" * 60)
    print("PHASE 9 — RAG DATA PREPROCESSING PIPELINE")
    print("=" * 60)
    
    if not DATASET_RAG_DIR.exists():
        raise FileNotFoundError(f"Source RAG dataset folder not found at: {DATASET_RAG_DIR}")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    processed_chunks = []
    total_documents = 0

    for folder_name in TARGET_FOLDERS:
        folder_path = DATASET_RAG_DIR / folder_name
        if not folder_path.exists():
            print(f"Warning: Directory '{folder_name}' missing in {DATASET_RAG_DIR}")
            continue

        pdf_files = list(folder_path.glob("*.pdf"))
        print(f"\nProcessing Folder: '{folder_name}' ({len(pdf_files)} PDF document(s))")

        for pdf_file in pdf_files:
            total_documents += 1
            file_name = pdf_file.name
            print(f"  - Reading document: {file_name}")

            try:
                reader = pypdf.PdfReader(pdf_file)
                raw_pages = []
                for p in reader.pages:
                    extracted = p.extract_text()
                    if extracted:
                        raw_pages.append(extracted)
                
                raw_full_text = "\n".join(raw_pages)
                clean_full_text = clean_text(raw_full_text)

                doc_title = extract_doc_title(file_name, raw_pages[0] if raw_pages else "")
                doc_chunks = chunk_text(clean_full_text)
                source_url = SOURCE_URL_MAP.get(file_name, f"https://www.niddk.nih.gov/health-information/{folder_name}")

                base_chunk_id = re.sub(r'[^a-zA-Z0-9_]', '_', file_name.lower().replace(".pdf", ""))

                for idx, text_chunk in enumerate(doc_chunks):
                    chunk_obj = {
                        "chunk_id": f"{folder_name}_{base_chunk_id}_{idx+1}",
                        "source": "NIDDK",
                        "source_url": source_url,
                        "title": doc_title,
                        "condition": folder_name,
                        "category": CATEGORY_MAP.get(folder_name, "General Health"),
                        "original_file": file_name,
                        "text": text_chunk
                    }
                    processed_chunks.append(chunk_obj)

                print(f"    -> Extracted {len(doc_chunks)} chunks (Raw chars: {len(raw_full_text)} -> Clean: {len(clean_full_text)})")

            except Exception as e:
                print(f"    [ERROR] Failed to process {file_name}: {e}")

    # Write output to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(processed_chunks, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Documents Processed : {total_documents}")
    print(f"Total Chunks Created      : {len(processed_chunks)}")
    print(f"Output File Path          : {OUTPUT_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    run_preprocessing_pipeline()
