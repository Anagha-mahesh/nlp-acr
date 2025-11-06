import os
import re
import pandas as pd
from tqdm import tqdm
import nltk

nltk.download('punkt', quiet=True)

DATA_DIR = "data/pure/cleaned"
OUTPUT_CSV = "outputs/smell_summary.csv"
os.makedirs("outputs", exist_ok=True)

AMBIGUOUS_WORDS = [
    "appropriate", "adequate", "as soon as possible", "normally", "reasonable",
    "sufficient", "some", "various", "typical", "often", "usually", "commonly"
]

VAGUE_WORDS = [
    "user[- ]?friendly", "fast", "efficient", "robust", "easy", "quick", "intuitive",
    "simple", "reliable", "powerful"
]

INCOMPLETE_PATTERNS = [
    r"etc\.?", r"and so on", r"to be determined", r"TBD", r"as required", r"if necessary"
]

def detect_smells(text, filename):
    sentences = nltk.sent_tokenize(text)
    results = []
    for sent in sentences:
        found = []
        if any(re.search(rf"\b{w}\b", sent, re.I) for w in AMBIGUOUS_WORDS):
            found.append("Ambiguity")
        if any(re.search(rf"\b{w}\b", sent, re.I) for w in VAGUE_WORDS):
            found.append("Vagueness")
        if any(re.search(p, sent, re.I) for p in INCOMPLETE_PATTERNS):
            found.append("Incompleteness")

        for f in found:
            results.append({"file": filename, "smell": f, "sentence": sent})
    return results

def main():
    all_results = []
    for file in tqdm(os.listdir(DATA_DIR)):
        if not file.endswith(".txt"):
            continue
        path = os.path.join(DATA_DIR, file)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        all_results.extend(detect_smells(text, file))

    df = pd.DataFrame(all_results)
    summary = df.groupby("smell")["file"].count().reset_index(name="count")
    summary.to_csv(OUTPUT_CSV, index=False)
    df.to_csv("outputs/smell_examples.csv", index=False)
    print(f"\n✅ Smell detection done. Summary saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()

