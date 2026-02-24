# cheesy-omission
Omission in cultural nuance MT
# When Not to Translate: Appropriate vs. Failure-Driven Omission in Culturally Nuanced Machine Translation

This repository contains the data and analysis code for:

> **"When Not to Translate: Appropriate vs. Failure-Driven Omission in Culturally Nuanced Machine Translation"**
> *Anonymous submission to Interspeech 2026*

This paper reanalyses the human evaluation dataset introduced in our companion paper (see [Related Work](#related-work)) by treating untranslated segments, typically excluded from MT quality analyses, as the primary outcome of interest. We identify two functionally distinct omission types: *appropriate omission*, where leaving content untranslated is the correct localisation decision, and *failure omission*, where models cannot produce adequate translations of figurative or culturally specific content.

---

## Repository Contents

```
.
├── README.md
├── Bombadil_Expansion_Data_-_clean.xlsx   # Raw annotation dataset (see Data)
├── strategic_omission_analysis.py         # Full analysis script (see Usage)
└── strategic_omission_tables.xlsx         # Summary tables reported in the paper
```

---

## Data

`Bombadil_Expansion_Data_-_clean.xlsx` contains the complete human annotation dataset: **13,125 segment-level annotations** collected from 75 native speakers across 15 target languages, evaluating translations produced by 7 multilingual LLMs.

### Dataset Structure

The spreadsheet is in wide format. Each row represents one rater's evaluation of one translated email, and contains:

| Column group | Description |
|---|---|
| Participant demographics | Age range, gender, education level |
| Language / Locale / Orthography | Target language and writing system |
| Model | The LLM that produced the translation |
| Email id | Which of the 5 source emails was evaluated (`email_1`–`email_5`) |
| Full-text ratings | Content fidelity, style fidelity, audience appropriateness (0–3 scale) |
| Overall quality | Holistic translation quality rating (0–3 scale) |
| Segment 1–5 | Segment text, category, translation, rating, and rater comments |

### Rating Scale

All ratings use a 0–3 ordinal scale:

| Value | Label |
|---|---|
| `3` | Very good or nearly perfect |
| `2` | Mostly good with small issues |
| `1` | Imperfect but not terrible |
| `0` | Serious failures exist |
| `na` | Segment not translated (omission) |

> **Important:** `na` encodes omission (the segment was left untranslated), not missing data. `0` is a valid quality rating meaning serious translation failure. This distinction is central to the analysis.

### Languages and Writing Systems

| Writing system | Languages |
|---|---|
| Alphabetic – Roman | Afrikaans, Brazilian Portuguese, Czech, Dutch, Spanish, Swahili |
| Alphabetic – Cyrillic | Russian |
| Alphabetic – Abjad | Arabic, Hebrew |
| Alphabetic – Abugida | Hindi, Urdu |
| Logographic | Cantonese, Mandarin |
| Syllabary | Japanese, Korean |

### Models Evaluated

| Model | Weight type |
|---|---|
| Claude Sonnet 4 | Closed-weight |
| GPT-5 | Closed-weight |
| Mistral Medium 3.1 | Closed-weight |
| Deepseek V3.1 | Closed-weight |
| gpt-oss 120b | Open-weight |
| Llama 4 | Open-weight |
| Cohere Aya Expanse 8B | Open-weight |

### Source Emails

Five English-language marketing emails were used as source texts, each containing five pre-selected segments of culturally nuanced language (25 segments total):

| Email | Brand | Category |
|---|---|---|
| email_1 | Sheffield's (gourmet market, NYC) | Valentine's Day |
| email_2 | Terra (eco-friendly deodorant) | New Year |
| email_3 | Muggable (novelty mugs) | General |
| email_4 | Sonia Summerhouse (luxury swimwear) | Labor Day / Summer |
| email_5 | Cinnamon (bakery & café) | Birthday |

Segments span four categories: **cultural concepts** (13), **idioms** (4), **puns** (4), and **holiday references** (4) per language.

---

## Usage

### Requirements

```
openpyxl
pandas
numpy
scipy
```

Install with:

```bash
pip install openpyxl pandas numpy scipy
```

### Running the Analysis

Place `Bombadil_Expansion_Data_-_clean.xlsx` in the same directory as the script, then:

```bash
python strategic_omission_analysis.py
```

The script will print all descriptive statistics, quality delta comparisons, and supporting analyses to the console, organised by paper section. It includes a verification block at the start that spot-checks key values against the paper's reported figures — all checks should return `[PASS]`.

### What the Script Computes

| Section | Contents |
|---|---|
| Data verification | Spot-checks against 5 key reported values |
| Table 1 | Omission rate and quality delta by segment category |
| Table 2 | Omission rate and quality delta by individual segment |
| Tables 3–4 | Per-model omission rates, NYE2026 vs. idiom diagnostic, open vs. closed weight comparison |
| Section 4.3 | NYE2026 and *Will you brie mine?* appropriate omission analyses, top failure-omission segments |
| Section 4.5 | Writing system and morphological type effects |

### A Note on IRR and CLMM

Inter-rater reliability (IRR) statistics and cumulative link mixed model (CLMM) estimates are **documented but not recomputed** in this script. These were produced in R using the `irr`, `irrCAC`, and `ordinal` packages as part of the companion paper analysis, and are cited from that work. Their exact values are stored in the `REPORTED_IRR` and `CLMM_ESTIMATES` dicts at the top of `strategic_omission_analysis.py` for reference and transparency.

---

## Key Findings

- **Omission is not a uniform failure mode.** NYE2026 (a promotional code) is omitted at 29.9% with no quality penalty (*p* = .479, *d* = −0.03), while idiom omission is associated with substantial quality degradation (*d* = 0.655).
- **Appropriate omission is robustly shared across models.** All seven models omit NYE2026 at similar rates (25–35%), regardless of capability tier.
- **Failure omission diverges sharply by capability.** Idiom omission ranges from 2.2% (GPT-5) to 44.9% (Cohere Aya Expanse 8B). Cohere is the only model where idiom omission exceeds NYE2026 omission (ratio: 1.77), indicating loss of the appropriate/failure distinction.
- **Open-weight models omit at nearly double the rate of closed-weight models** (10.6% vs. 5.9%) and incur a larger quality penalty when they do (*d* = 0.461 vs. 0.179).
- **Writing system modulates quality loss** when failure omission occurs, but not omission rates themselves.

---

## Related Work

This repository accompanies a companion paper that introduced the evaluation benchmark:

> **"Be My Cheese? Cultural Nuance Benchmarking for Machine Translation in Multilingual LLMs"**
> *Anonymous submission, under review*

That paper describes the full benchmark design, annotation protocol, CLMM specification, and IRR analysis. The present work reanalyses the same dataset with omission as the primary outcome variable rather than excluding it.

---

## Citation

If you use this data or code, please cite both papers (citations will be updated upon acceptance):

```bibtex
@inproceedings{anonymous2026omission,
  title     = {When Not to Translate: Appropriate vs. Failure-Driven Omission
               in Culturally Nuanced Machine Translation},
  author    = {Anonymous},
  booktitle = {Proceedings of Interspeech 2026},
  year      = {2026}
}

@article{anonymous2025cheese,
  title  = {Be My Cheese? Cultural Nuance Benchmarking for Machine Translation
            in Multilingual LLMs},
  author = {Anonymous},
  year   = {2025},
  note   = {Under review}
}
```

---

## License

To be confirmed upon de-anonymisation.
