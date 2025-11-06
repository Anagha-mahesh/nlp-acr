# **NLP Assignment 5**
**Abbreviation and Subjective Terms Checker**

- `data/pure/cleaned` contains PURE SRS data in `*.txt` format  
- `/scripts` contains all necessary scripts  
- `/outputs` contains the outputs generated in `*.csv` format  

**Run Command:**  
```bash
pip install requirements.txt
python abbr_checker_2.py
```
**Generated output files:** 
- `abbreviation_glossary.csv`        : acronym, expansion, file, sent_idx, sentence
- `abbrev_issues.csv`                : file, acronym, issue, sent_idx, sentence, guessed_expansion
- `abbrev_inconsistencies.csv`       : issue, key, details
- `subjective_flags.csv`             : file, sent_idx, term, sentence, suggestion
- `assignment5_stats.csv`            : summary stats (counts)
