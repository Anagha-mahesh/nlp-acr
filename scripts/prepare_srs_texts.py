import os
import pdfplumber
from bs4 import BeautifulSoup
from striprtf.striprtf import rtf_to_text
from tqdm import tqdm

SOURCE_DIR = "data/pure/req"
OUTPUT_DIR = "data/pure/cleaned"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_html(path):
    with open(path, "r", encoding="latin-1", errors="ignore") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n")

def extract_rtf(path):
    with open(path, "r", encoding="latin-1", errors="ignore") as f:
        content = f.read()
    return rtf_to_text(content)

def clean_text(text):
    text = text.replace("\r", "\n")
    text = " ".join(text.split())
    return text.strip()

extractors = {
    ".pdf": extract_pdf,
    ".html": extract_html,
    ".htm": extract_html,
    ".rtf": extract_rtf,
}

def main():
    errors = []
    for filename in tqdm(os.listdir(SOURCE_DIR)):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in extractors:
            continue  # skip .doc files
        src_path = os.path.join(SOURCE_DIR, filename)
        try:
            text = extractors[ext](src_path)
            cleaned = clean_text(text)
            out_path = os.path.join(OUTPUT_DIR, filename.replace(ext, ".txt"))
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(cleaned)
        except Exception as e:
            errors.append((filename, str(e)))

    print(f"\n Extraction complete. Cleaned files saved to {OUTPUT_DIR}")
    if errors:
        print("\n Some files failed to process:")
        for f, err in errors:
            print(f" - {f}: {err}")

if __name__ == "__main__":
    main()
