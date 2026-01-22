import os
import json
import pdfplumber
from tqdm import tqdm

# --- CONFIGURATION ---
INPUT_DIR = "data/raw"
OUTPUT_FILE = "data/processed/train.jsonl"
CHUNK_SIZE = 1000 
OVERLAP = 200     

def clean_text(text):
    """
    Why this? Raw PDF text is messy. It has extra spaces, newlines, 
    and weird artifacts. This standardizes it.
    """
    if not text:
        return ""
    text = " ".join(text.split())
    return text

def chunk_text(text, chunk_size, overlap):
    """
    Why this? LLMs have a "Context Window" (memory limit). 
    We can't feed a whole book at once. We break it into bite-sized pieces.
    
    Why Overlap? If a sentence is cut in half at the end of chunk 1, 
    the model loses meaning. Overlap ensures the full sentence appears in chunk 2.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += (chunk_size - overlap) 
    return chunks

def process_pdfs():
    print(f"Starting PDF extraction from {INPUT_DIR}...")
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.pdf')]
    
    all_data = []

    # Loop through each PDF (using tqdm for a progress bar)
    for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
        pdf_path = os.path.join(INPUT_DIR, pdf_file)
        full_text = ""
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    # Extract text from the page
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + " "
            
            # Clean the raw text
            clean_full_text = clean_text(full_text)
            
            # Create chunks
            chunks = chunk_text(clean_full_text, CHUNK_SIZE, OVERLAP)
            
            for chunk in chunks:
                entry = {
                    "instruction": f"Extract technical information from the {pdf_file} documentation.",
                    "input": "",
                    "output": chunk
                }
                all_data.append(entry)
                
        except Exception as e:
            print(f"Error processing {pdf_file}: {e}")

    print(f"Saving {len(all_data)} chunks to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for entry in all_data:
            json.dump(entry, f)
            f.write('\n')
            
    print("Done! Data preparation complete.")

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    process_pdfs()