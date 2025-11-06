import os
from pathlib import Path
from collections import Counter

DATA_DIR = Path("data/pure/req")

def file_summary(path):
    types = []
    counts = Counter()
    for p in path.rglob("*"):
        if p.is_file():
            ext = p.suffix.lower() or "<noext>"
            counts[ext] += 1
            types.append(ext)
    return counts

def preview_files(path, n=5):
    previews = []
    files = sorted([p for p in path.rglob("*") if p.is_file()])[:n]
    for p in files:
        try:
            if p.suffix.lower() in [".txt", ".md", ".html", ".htm", ".xml", ".json"]:
                content = p.read_text(errors="ignore")[:200]
            else:
                content = f"<binary / non-text file: {p.suffix}>"
        except Exception as e:
            content = f"<error reading: {e}>"
        previews.append((str(p), content))
    return previews

if __name__ == "__main__":
    if not DATA_DIR.exists():
        print(f"Dataset directory {DATA_DIR} not found. Please download PURE and place it there.")
        raise SystemExit(1)

    counts = file_summary(DATA_DIR)
    print("File type counts in data/pure")
    for ext,count in counts.most_common():
        print(f"  {ext:6} : {count}")

    print("\nSample file previews:")
    for p,preview in preview_files(DATA_DIR, n=10):
        print("----", p)
        print(preview)
        print()
