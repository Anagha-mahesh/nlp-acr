#Assignment 5 — Abbreviation Completeness & Subjective Terms Checker

import os, re, csv
from collections import defaultdict, OrderedDict, Counter
from tqdm import tqdm

INPUT_DIR = "data/pure/cleaned"
OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

# Subjective terms
SUBJECTIVE_MAP = {
    "user-friendly": "Replace with measurable usability criteria, e.g., 'Novice user completes task X in ≤ 90s with ≥90% success.'",
    "user friendly": "Replace with measurable usability criteria, e.g., 'Novice user completes task X in ≤ 90s with ≥90% success.'",
    "fast": "Replace with quantifiable timing, e.g., 'Response time ≤ 200 ms under N concurrent users.'",
    "efficient": "Replace with resource bound, e.g., 'CPU ≤ 10% at normal load' or 'throughput ≥ 100 req/s'.",
    "intuitive": "Replace with usability metric, e.g., 'Task success rate ≥ 85% in usability test.'",
    "simple": "Replace with concrete steps or complexity limit, e.g., '≤ 3 steps to complete X'.",
    "robust": "Specify failure modes and recovery time, e.g., 'recovers within 5s after transient failure'.",
    "reliable": "Specify reliability target, e.g., 'availability ≥ 99.9% monthly'.",
    "secure": "Specify exact controls / standards, e.g., 'TLS1.2+; AES-256 for data at rest'.",
    "scalable": "Quantify scale, e.g., 'supports 10k concurrent users with <X latency'.",
    "easy": "Specify what 'easy' means (install, learn, use) with measurable criteria."
}

# Patterns: "Expansion (ACR)" and "ACR (Expansion)"
PAT_EXPANSION_ACR = re.compile(r'\b([A-Za-z][A-Za-z0-9&\-\s]{1,120}?)\s*\(\s*([A-Z][A-Z0-9\.\-]{1,8})\s*\)')
PAT_ACR_EXPANSION = re.compile(r'\b([A-Z][A-Z0-9\.\-]{1,8})\s*\(\s*([A-Za-z][A-Za-z0-9&\-\s]{1,120}?)\s*\)')

# Token regex for scanning possible acronyms
TOKEN_RE = re.compile(r'\b[A-Za-z0-9\.\-]{2,10}\b')

# Header/stop words 
COMMON_STOPWORDS = {
    "THE","AND","OF","IN","ON","AT","FOR","BY","TO","WITH","AN","A","AS","IS","IT","THIS","THAT",
    "ALL","ONCE","USING","AFTER","BEFORE","FROM","PAGE","HOME","MODULE","SYSTEM","SECTION","TABLE",
    "REQUIREMENTS","DESCRIPTION","OVERVIEW","INTRODUCTION","SCOPE","SUMMARY","CORE"
}

# avoid bibliography/URL noise
BIB_NOISE_KEYWORDS = [r'http[s]?://', r'www\.', r'ISBN', r'Publisher:', r'Edition:', r'ISBN:', r'ISBN\b', r'doi:', r'Published']
SKIP_DOMAIN_EXTS = {"com","org","net","htm","html","php","asp","jsp","txt","pdf","xml","db","sql"}
NOISY_UPPER_TOKENS = {"THEGNU","ANALAN","PVWAVE","NONE","ACTIVE","EMEANS","BCOST","ISUNIX","FUSE","LEVEL","SEE"}

def normalize_acr_token(token: str) -> str:
    """Normalize tokens like 'U.S.A.' or 'U S A' -> 'USA' and uppercase."""
    t = token.replace(".", "").replace(" ", "").strip()
    t = re.sub(r'^[^A-Za-z0-9]+|[^A-Za-z0-9]+$', '', t)
    return t.upper()

def is_heading_sentence(s: str, length_threshold=60, uppercase_ratio_threshold=0.6):
    if not s or not s.strip():
        return True
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return False
    upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    if len(s) < length_threshold and upper_ratio >= uppercase_ratio_threshold:
        return True
    return False

def split_sentences(text: str):
    #splitting on punctuation and newlines
    sents = re.split(r'(?<=[\.\?!])\s+|\n+', text)
    return [s.strip() for s in sents if s and s.strip()]

def _is_bibliography_or_url_heavy(sent: str):
    for p in BIB_NOISE_KEYWORDS:
        if re.search(p, sent, re.IGNORECASE):
            return True
    up_tokens = [w for w in re.findall(r'\b[A-Z][A-Z0-9\-]{1,}\b', sent)]
    if len(up_tokens) >= 4:
        return True
    if len(re.findall(r'\d{2,}', sent)) >= 2 and len(sent) > 80:
        return True
    if sent.count('/') >= 2 or sent.count(':') >= 3:
        return True
    return False

def find_acronyms_in_sentence(sent: str):
    if is_heading_sentence(sent):
        return []

    if _is_bibliography_or_url_heavy(sent):
        return []

    tokens = TOKEN_RE.findall(sent)
    found = []

    paren_matches = re.findall(r'\(([A-Za-z0-9\.\-]{2,20})\)', sent)
    for p in paren_matches:
        if re.match(r'^[0-9]+$', p):
            continue
        if p.lower() in SKIP_DOMAIN_EXTS:
            continue
        # skip if it's all lowercase or only first letter uppercase
        if p.islower() or (p[0].isupper() and p[1:].islower()):
            continue
        if len(p) > 6 and p.isalpha() and p[0].isupper() and p[1:].islower():
            continue
        if not (sum(1 for c in p if c.isupper()) >= 2 or '.' in p or re.search(r'[A-Z][a-z]+[A-Z]', p)):
            continue

        normp = normalize_acr_token(p)
        if 2 <= len(normp) <= 10 and normp.isalpha() and normp not in COMMON_STOPWORDS and normp not in NOISY_UPPER_TOKENS:
            found.append(normp)


    LATIN_SKIP = {"EG", "IE", "ETC", "AKA", "VS"}
    HEADING_SKIP = {"REQUIREMENTS", "MODE", "USERS", "TEST","WWW", "WWWFS"}

    for tok in tokens:
        orig = tok.strip()
        if re.search(r'http[s]?://|www\.|\.(com|org|net|htm|html|php|asp|jsp|txt|pdf|xml)\b', orig, re.IGNORECASE):
            continue
        norm = normalize_acr_token(orig)
        if re.search(r'\d$', orig):
            continue
        if not norm.isalpha():
            continue
        if not (2 <= len(norm) <= 6):
            continue
        if re.match(r'^[A-Za-z]\.?[A-Z]', orig):
            continue
        if norm in LATIN_SKIP or norm in HEADING_SKIP:
            continue
        if norm in NOISY_UPPER_TOKENS:
            continue
        if re.match(r'^[A-Z]{2,}$', orig) and re.match(r'^\s*[A-Z]{2,}', sent):
            continue

        up_count = sum(1 for c in orig if c.isupper())
        candidate_flag = False

        if '.' in orig:
            candidate_flag = True
        elif up_count >= 2:
            candidate_flag = True
        elif orig.isupper() and len(norm) <= 6:
            candidate_flag = True

        if not candidate_flag:
            continue

        if norm in COMMON_STOPWORDS:
            continue

        found.append(norm)

    seen, uniq = set(), []
    for a in found:
        if a not in seen:
            uniq.append(a)
            seen.add(a)

    return uniq


def guess_expansion_nearby(sentences, sent_idx, acr):
    start = max(0, sent_idx-1)
    end = min(len(sentences), sent_idx+2)
    for i in range(start, end):
        s = sentences[i]

        matches = re.findall(r'((?:[A-Z][a-z0-9_\-]{2,}\s+){1,5}[A-Z][a-z0-9_\-]{2,})', s)
        for m in matches:
            candidate = m.strip()
            if candidate and candidate[0].upper() == acr[0]:
                return candidate
    return ""

glossary_rows = []            # for abbreviation_glossary.csv
issues_rows = []              # for abbrev_issues.csv
inconsistency_rows = []       # for abbrev_inconsistencies.csv
subjective_rows = []          # subjective_flags.csv

acr_to_expansions = defaultdict(set)   # acr -> set(expansions)
expansion_to_acrs = defaultdict(set)   # expansion -> set(acrs)
unique_acr_occurrences = defaultdict(int)  # acr -> total count across corpus
unique_subjective_terms = Counter()

# iterate files
files = sorted([f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".txt")])
for fname in tqdm(files, desc="Processing files"):
    path = os.path.join(INPUT_DIR, fname)
    raw = ""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            raw = fh.read()
    except Exception:
        continue

    sentences = split_sentences(raw)
    acr_defs_doc = OrderedDict()
    acr_occ_doc = defaultdict(list)

    for i, s in enumerate(sentences):
        for m in PAT_EXPANSION_ACR.finditer(s):
            exp = m.group(1).strip()
            acr_raw = m.group(2).strip()
            acr = normalize_acr_token(acr_raw)
            if acr not in acr_defs_doc:
                acr_defs_doc[acr] = (exp, i, s)
                acr_to_expansions[acr].add(exp)
                expansion_to_acrs[exp].add(acr)
        for m in PAT_ACR_EXPANSION.finditer(s):
            acr_raw = m.group(1).strip()
            exp = m.group(2).strip()
            acr = normalize_acr_token(acr_raw)
            if acr not in acr_defs_doc:
                acr_defs_doc[acr] = (exp, i, s)
                acr_to_expansions[acr].add(exp)
                expansion_to_acrs[exp].add(acr)

    for i, s in enumerate(sentences):
        acrs = find_acronyms_in_sentence(s)
        for a in acrs:
            acr_occ_doc[a].append(i)

        for term, suggestion in SUBJECTIVE_MAP.items():
            if re.search(r'\b' + re.escape(term) + r'\b', s, re.I):
                subjective_rows.append({
                    "file": fname,
                    "sent_idx": i,
                    "term": term,
                    "sentence": s,
                    "suggestion": suggestion
                })
                unique_subjective_terms[term] += 1


    def appears_dotted_or_parenthesized(raw_text, acr_upper):
        parts = list(acr_upper)
        dot_pattern = r'\.?'.join(map(re.escape, parts)) + r'\.?'
        pattern = r'(' + dot_pattern + r')'
        return re.search(pattern, raw_text, re.IGNORECASE) is not None

    filtered_acr_occ_doc = {}
    for a, occs in acr_occ_doc.items():
        if a in acr_defs_doc:
            filtered_acr_occ_doc[a] = occs
            continue
        if len(occs) > 1:
            filtered_acr_occ_doc[a] = occs
            continue
        if appears_dotted_or_parenthesized(raw, a):
            filtered_acr_occ_doc[a] = occs
            continue

    acr_occ_doc = filtered_acr_occ_doc

    for a, occs in acr_occ_doc.items():
        unique_acr_occurrences[a] += len(occs)

    for acr, (exp, idx, sent) in acr_defs_doc.items():
        glossary_rows.append({
            "acronym": acr,
            "expansion": exp,
            "file": fname,
            "sent_idx": idx,
            "sentence": sent
        })

    for acr, occs in acr_occ_doc.items():
        if acr not in acr_defs_doc:
            first_idx = min(occs)
            context_sent = sentences[first_idx] if first_idx < len(sentences) else ""
            guessed = guess_expansion_nearby(sentences, first_idx, acr)
            issues_rows.append({
                "file": fname,
                "acronym": acr,
                "issue": "undefined_in_document",
                "sent_idx": first_idx,
                "sentence": context_sent,
                "guessed_expansion": guessed
            })
        else:
            def_idx = acr_defs_doc[acr][1]
            first_idx = min(occs)
            if first_idx < def_idx:
                context_sent = sentences[first_idx] if first_idx < len(sentences) else ""
                guessed = "" 
                issues_rows.append({
                    "file": fname,
                    "acronym": acr,
                    "issue": "first_use_before_definition",
                    "sent_idx": first_idx,
                    "sentence": context_sent,
                    "guessed_expansion": guessed
                })

for acr, exps in acr_to_expansions.items():
    if len(exps) > 1:
        inconsistency_rows.append({
            "issue": "acronym_multiple_expansions",
            "key": acr,
            "details": "; ".join(sorted(exps))
        })
for exp, acrs in expansion_to_acrs.items():
    if len(acrs) > 1:
        inconsistency_rows.append({
            "issue": "expansion_multiple_acronyms",
            "key": exp,
            "details": "; ".join(sorted(acrs))
        })

# abbreviation_glossary.csv
with open(os.path.join(OUT_DIR, "abbreviation_glossary.csv"), "w", newline="", encoding="utf-8") as fo:
    writer = csv.DictWriter(fo, fieldnames=["acronym", "expansion", "file", "sent_idx", "sentence"])
    writer.writeheader()
    for r in glossary_rows:
        writer.writerow(r)

# abbrev_issues.csv
with open(os.path.join(OUT_DIR, "abbrev_issues.csv"), "w", newline="", encoding="utf-8") as fo:
    writer = csv.DictWriter(fo, fieldnames=["file", "acronym", "issue", "sent_idx", "sentence", "guessed_expansion"])
    writer.writeheader()
    for r in issues_rows:
        writer.writerow(r)

# abbrev_inconsistencies.csv
with open(os.path.join(OUT_DIR, "abbrev_inconsistencies.csv"), "w", newline="", encoding="utf-8") as fo:
    writer = csv.DictWriter(fo, fieldnames=["issue", "key", "details"])
    writer.writeheader()
    for r in inconsistency_rows:
        writer.writerow(r)

# subjective_flags.csv
with open(os.path.join(OUT_DIR, "subjective_flags.csv"), "w", newline="", encoding="utf-8") as fo:
    writer = csv.DictWriter(fo, fieldnames=["file", "sent_idx", "term", "sentence", "suggestion"])
    writer.writeheader()
    for r in subjective_rows:
        writer.writerow(r)

# assignment5_stats.csv
unique_acrs = set(unique_acr_occurrences.keys())
stats = {
    "total_files_processed": len(files),
    "total_acronym_occurrences_with_duplicates": sum(unique_acr_occurrences.values()),
    "total_unique_acronyms": len(unique_acrs),
    "total_missing_definitions_unique": len({(r['file'], r['acronym']) for r in issues_rows if r['issue']=="undefined_in_document"}),
    "total_missing_definitions_with_duplicates": sum(1 for r in issues_rows if r['issue']=="undefined_in_document"),
    "total_first_use_before_definition_unique": len({(r['file'], r['acronym']) for r in issues_rows if r['issue']=="first_use_before_definition"}),
    "total_inconsistencies_acronym_multiple_expansions": sum(1 for r in inconsistency_rows if r['issue']=="acronym_multiple_expansions"),
    "total_inconsistencies_expansion_multiple_acronyms": sum(1 for r in inconsistency_rows if r['issue']=="expansion_multiple_acronyms"),
    "subjective_terms_with_duplicates": sum(unique_subjective_terms.values()),
    "subjective_terms_unique": len(unique_subjective_terms)
}

with open(os.path.join(OUT_DIR, "assignment5_stats.csv"), "w", newline="", encoding="utf-8") as fo:
    writer = csv.writer(fo)
    writer.writerow(["metric", "count"])
    for k, v in stats.items():
        writer.writerow([k, v])

# final print
print("Assignment 5 complete. Outputs written to:", OUT_DIR)
print("Files produced:")
print(" - abbreviation_glossary.csv")
print(" - abbrev_issues.csv")
print(" - abbrev_inconsistencies.csv")
print(" - subjective_flags.csv")
print(" - assignment5_stats.csv")
