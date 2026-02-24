"""
Strategic Omission Analysis
============================
"When Not to Translate: Appropriate vs. Failure-Driven Omission in
Culturally Nuanced Machine Translation"

This script reproduces all descriptive statistics, quality delta comparisons,
and supporting analyses reported in the paper. It reads from the raw annotation
data (Bombadil_Expansion_Data_-_clean.xlsx) and outputs results to the console.

Data encoding notes:
- segment_rating: 0-3 ordinal quality scale (0 = serious failure, 3 = very good)
- segment_rating == 'na': segment was not translated (omission)
- overall_quality: 0-3 holistic email quality rating
- One anomalous value (905) in segment_rating is removed as a data entry error.

IRR statistics (Krippendorff's alpha, Gwet's AC2) are drawn directly from
the parent paper [4] (Be My Cheese? Cultural Nuance Benchmarking for Machine
Translation in Multilingual LLMs) and are cited rather than recomputed here,
as they require the irrCAC R package. Key values are documented in the
REPORTED_IRR dict below.

CLMM estimates are likewise drawn from Table C1 of [4] and documented in
CLMM_ESTIMATES below. The CLMM was fitted in R using the ordinal package
(Christensen, 2022) with fixed effects for model, language, and segment
category, and random intercepts for annotator and segment.

Dependencies: openpyxl, pandas, numpy, scipy
"""

import openpyxl
import pandas as pd
import numpy as np
from scipy import stats


# ---------------------------------------------------------------------------
# IRR values from parent paper [4], Table C8
# ---------------------------------------------------------------------------
REPORTED_IRR = {
    "overall_segment": {
        "krippendorff_alpha": 0.448,
        "gwet_ac2": 0.412,
    },
    "by_category": {
        "cultural concepts": {"krippendorff_alpha": 0.441, "gwet_ac2": 0.348},
        "holidays":          {"krippendorff_alpha": 0.380, "gwet_ac2": 0.406},
        "idioms":            {"krippendorff_alpha": 0.405, "gwet_ac2": 0.107},
        "puns":              {"krippendorff_alpha": 0.307, "gwet_ac2": 0.263},
    },
}

# ---------------------------------------------------------------------------
# Key CLMM estimates from parent paper [4], Table C1
# CLMM: cumulative link mixed model (logit link), ordinal package in R
# Reference levels: GPT-5 (model), Afrikaans (language), cultural concepts (category)
# Random intercepts: annotator, segment
# logLik = -14411.63, AIC = 28965.26, n = 13125
# ---------------------------------------------------------------------------
CLMM_ESTIMATES = {
    "model_cohere_aya_8b":   {"beta": 1.90, "se": 0.15, "p": "<.001"},
    "model_deepseek_v3.1":   {"beta": 0.51, "se": 0.15, "p": ".001"},
    "model_gpt5":            {"beta": 0.02, "se": 0.16, "p": ".878"},   # ref: not sig
    "model_gpt_oss_120b":    {"beta": 0.81, "se": 0.15, "p": "<.001"},
    "model_llama4":          {"beta": 1.03, "se": 0.15, "p": "<.001"},
    "model_mistral_3.1":     {"beta": 0.38, "se": 0.15, "p": ".013"},
    "segment_category_L":    {"beta": 1.66, "se": 0.08, "p": "<.001"},
    "segment_category_Q":    {"beta": 0.31, "se": 0.10, "p": ".001"},
    "segment_category_C":    {"beta": -0.84,"se": 0.11, "p": "<.001"},
    "language_mandarin":     {"beta": -1.53,"se": 0.49, "p": ".002"},
    "random_sd_segment":     0.70,
    "random_sd_annotator":   1.76,
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def cohen_d(a: pd.Series, b: pd.Series) -> float:
    """Pooled-SD Cohen's d (a - b)."""
    pooled_sd = np.sqrt((a.std() ** 2 + b.std() ** 2) / 2)
    if pooled_sd == 0:
        return np.nan
    return (a.mean() - b.mean()) / pooled_sd


def quality_delta_stats(group: pd.DataFrame, label: str = "") -> dict:
    """
    Compare overall_quality between translated and omitted segments.
    Returns dict with means, delta, Cohen's d, t, and p.
    """
    trans = group[~group["is_omitted"]]["overall_quality"].dropna()
    omit  = group[group["is_omitted"]]["overall_quality"].dropna()
    delta = trans.mean() - omit.mean()
    d     = cohen_d(trans, omit)
    t, p  = stats.ttest_ind(trans, omit)
    return {
        "label":         label,
        "n_total":       len(group),
        "n_omitted":     int(group["is_omitted"].sum()),
        "omit_rate":     group["is_omitted"].mean(),
        "overall_trans": trans.mean(),
        "overall_omit":  omit.mean() if len(omit) > 0 else np.nan,
        "delta":         delta,
        "cohen_d":       d,
        "t":             t,
        "p":             p,
    }


def print_section(title: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print("=" * 70)


def print_subsection(title: str) -> None:
    print(f"\n--- {title} ---")


# ---------------------------------------------------------------------------
# Load and prepare data
# ---------------------------------------------------------------------------

def load_data(filepath: str) -> pd.DataFrame:
    """
    Load the wide-format annotation spreadsheet and melt to long format
    (one row per segment annotation).
    """
    wb = openpyxl.load_workbook(filepath)
    ws = wb["clean_final"]
    headers = [cell.value for cell in ws[1]]
    data = list(ws.iter_rows(min_row=2, values_only=True))
    wide = pd.DataFrame(data, columns=headers)

    overall_col = (
        "Considering both the overall translation, and the specific segments "
        "evaluated, what is the overall quality of this translation?"
    )

    records = []
    for _, row in wide.iterrows():
        base = {
            "language":       row["Language"],
            "orthography":    row["Orthography"],
            "model":          row["Model"],
            "email":          row["Email id"],
            "overall_quality": row[overall_col],
        }
        for s in range(1, 6):
            r = base.copy()
            r["segment"]          = row.get(f"Segment {s}")
            r["segment_rating"]   = row.get(f"Segment {s} rating")
            r["segment_category"] = str(row.get(f"Segment {s} category", "")).strip()
            r["segment_translation"] = row.get(f"Segment {s} translation")
            records.append(r)

    long = pd.DataFrame(records)

    # Remove data entry error
    long = long[long["segment_rating"] != 905].copy()

    # Derived columns
    long["is_omitted"]     = long["segment_rating"] == "na"
    long["seg_quality"]    = pd.to_numeric(long["segment_rating"], errors="coerce")
    long["overall_quality"] = pd.to_numeric(long["overall_quality"], errors="coerce")

    # Normalise orthography
    long["orthography"] = long["orthography"].replace("Roman", "Alphabetic - Roman")
    long.loc[long["language"] == "Russian", "orthography"] = "Alphabetic - Cyrillic"

    return long


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def verify_against_paper(long: pd.DataFrame) -> None:
    """
    Spot-checks against key reported values to confirm data integrity.
    All values should match the paper exactly.
    """
    print_section("DATA VERIFICATION (spot-checks against paper)")

    checks = {
        "NYE2026 omission rate (paper: 29.9%)": (
            long[long["segment"] == "NYE2026"]["is_omitted"].mean(), 0.299
        ),
        "Cohere overall omit rate (paper: 14.8%)": (
            long[long["model"] == "Cohere Aya Expanse 8B"]["is_omitted"].mean(), 0.148
        ),
        "GPT-5 overall omit rate (paper: 6.5%)": (
            long[long["model"] == "GPT-5"]["is_omitted"].mean(), 0.065
        ),
        "Cohere idiom omit rate (paper: 44.9%)": (
            long[(long["model"] == "Cohere Aya Expanse 8B") &
                 (long["segment_category"] == "idioms")]["is_omitted"].mean(), 0.449
        ),
        "Cultural concepts omit rate (paper: 5.8%)": (
            long[long["segment_category"] == "cultural concepts"]["is_omitted"].mean(), 0.058
        ),
    }

    all_pass = True
    for name, (actual, expected) in checks.items():
        ok = abs(actual - expected) < 0.002
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        print(f"  [{status}] {name}: {actual:.3f} (expected {expected:.3f})")

    if all_pass:
        print("\n  All verification checks passed.")
    else:
        print("\n  WARNING: Some checks failed. Investigate before reporting.")


def table1_category_omission(long: pd.DataFrame) -> None:
    """Table 1: Omission rate and quality delta by segment category."""
    print_section("TABLE 1: OMISSION RATE AND QUALITY DELTA BY SEGMENT CATEGORY")
    print(f"  {'Category':<22} {'N':>6} {'N_omit':>7} {'Omit%':>7} "
          f"{'SegQ(trans)':>12} {'OvQ(trans)':>11} {'OvQ(omit)':>10} "
          f"{'Delta':>7} {'d':>7} {'p':>9}")
    print("  " + "-" * 105)

    for cat in ["cultural concepts", "holidays", "idioms", "puns"]:
        sub = long[long["segment_category"] == cat]
        res = quality_delta_stats(sub, cat)
        seg_q = sub[~sub["is_omitted"]]["seg_quality"].mean()
        p_str = f"{res['p']:.3f}" if res["p"] >= 0.001 else "<.001"
        print(
            f"  {cat:<22} {res['n_total']:>6} {res['n_omitted']:>7} "
            f"{res['omit_rate']:>6.1%} {seg_q:>12.2f} "
            f"{res['overall_trans']:>11.2f} {res['overall_omit']:>10.2f} "
            f"{res['delta']:>7.3f} {res['cohen_d']:>7.3f} {p_str:>9}"
        )


def table2_segment_omission(long: pd.DataFrame) -> None:
    """Table 2: Omission rate and quality delta by individual segment."""
    print_section("TABLE 2: OMISSION RATE AND QUALITY DELTA BY SEGMENT")
    print(f"  {'Category':<22} {'Segment':<35} {'N_omit':>7} {'Omit%':>7} "
          f"{'Delta':>7} {'d':>7} {'p':>9}")
    print("  " + "-" * 100)

    for cat in ["cultural concepts", "holidays", "idioms", "puns"]:
        cat_df = long[long["segment_category"] == cat]
        segs = (cat_df.groupby("segment")["is_omitted"]
                .mean()
                .sort_values(ascending=False)
                .index.tolist())
        for seg in segs:
            sub = long[long["segment"] == seg]
            if sub.empty:
                continue
            res = quality_delta_stats(sub, seg)
            p_str = f"{res['p']:.3f}" if res["p"] >= 0.001 else "<.001"
            print(
                f"  {cat:<22} {seg:<35} {res['n_omitted']:>7} "
                f"{res['omit_rate']:>6.1%} {res['delta']:>7.3f} "
                f"{res['cohen_d']:>7.3f} {p_str:>9}"
            )


def model_level_effects(long: pd.DataFrame) -> None:
    """Table 3/4: Omission and quality delta by model and weight type."""
    print_section("TABLES 3–4: MODEL-LEVEL OMISSION AND QUALITY EFFECTS")

    closed = ["Claude Sonnet 4", "GPT-5", "Mistral Medium 3.1", "Deepseek V3.1"]
    open_w = ["gpt-oss 120b", "Llama 4", "Cohere Aya Expanse 8B"]

    print_subsection("Per-model omission rates and NYE2026 vs idiom diagnostic")
    print(f"  {'Model':<25} {'Type':<8} {'Overall':>8} {'NYE2026':>9} "
          f"{'Idioms':>8} {'Ratio':>7}")
    print("  " + "-" * 72)

    for model in closed + open_w:
        sub   = long[long["model"] == model]
        wtype = "Closed" if model in closed else "Open"
        omit  = sub["is_omitted"].mean()
        nye   = sub[sub["segment"] == "NYE2026"]["is_omitted"].mean()
        idiom = sub[sub["segment_category"] == "idioms"]["is_omitted"].mean()
        ratio = idiom / max(nye, 1e-6)
        print(f"  {model:<25} {wtype:<8} {omit:>7.1%} {nye:>8.1%} "
              f"{idiom:>7.1%} {ratio:>7.2f}")

    print_subsection("Open vs closed weight: omission rate and quality delta")
    for label, models in [("Closed", closed), ("Open", open_w)]:
        sub = long[long["model"].isin(models)]
        res = quality_delta_stats(sub, label)
        print(f"  {label}: omit={res['omit_rate']:.1%}, "
              f"overall(trans)={res['overall_trans']:.2f}, "
              f"overall(omit)={res['overall_omit']:.2f}, "
              f"d={res['cohen_d']:.3f}")

    print_subsection("Quality delta by category, split by weight type")
    print(f"  {'Weight':<8} {'CC delta':>10} {'Holiday delta':>14} "
          f"{'Idiom delta':>12} {'Pun delta':>10}")
    print("  " + "-" * 58)
    for label, models in [("Closed", closed), ("Open", open_w)]:
        deltas = []
        for cat in ["cultural concepts", "holidays", "idioms", "puns"]:
            sub = long[long["model"].isin(models) & (long["segment_category"] == cat)]
            res = quality_delta_stats(sub)
            deltas.append(f"{res['delta']:>10.3f}")
        print(f"  {label:<8} {'  '.join(deltas)}")

    print_subsection("CLMM convergence (from parent paper [4], Table C1)")
    print(f"  Cohere Aya Expanse 8B: β = {CLMM_ESTIMATES['model_cohere_aya_8b']['beta']}, "
          f"SE = {CLMM_ESTIMATES['model_cohere_aya_8b']['se']}, "
          f"p {CLMM_ESTIMATES['model_cohere_aya_8b']['p']} (vs GPT-5 reference)")
    print(f"  Llama 4:               β = {CLMM_ESTIMATES['model_llama4']['beta']}, "
          f"SE = {CLMM_ESTIMATES['model_llama4']['se']}, "
          f"p {CLMM_ESTIMATES['model_llama4']['p']}")
    print("  Note: CLMM conditions on translated segments only (omissions excluded).")
    print("  Cohere quality disadvantage persisting in CLMM confirms genuine")
    print("  translation failure, not elevated omission rates alone.")


def appropriate_vs_failure_omission(long: pd.DataFrame) -> None:
    """Section 4.3: NYE2026 and brie mine appropriate omission analysis."""
    print_section("SECTION 4.3: APPROPRIATE VS FAILURE-DRIVEN OMISSION")

    print_subsection("NYE2026 (appropriate omission)")
    nye = long[long["segment"] == "NYE2026"]
    res = quality_delta_stats(nye, "NYE2026")
    p_str = f"{res['p']:.3f}"
    print(f"  Omission rate: {res['omit_rate']:.1%} (n omitted = {res['n_omitted']})")
    print(f"  Overall quality (translated): {res['overall_trans']:.2f}")
    print(f"  Overall quality (omitted):    {res['overall_omit']:.2f}")
    print(f"  Delta: {res['delta']:.3f}, d = {res['cohen_d']:.3f}, p = {p_str}")
    print(f"  Interpretation: no significant quality penalty; appropriate omission.")

    print_subsection("NYE2026 omission rate by writing system")
    for orth in long["orthography"].dropna().unique():
        sub = long[(long["segment"] == "NYE2026") & (long["orthography"] == orth)]
        if sub.empty:
            continue
        res = quality_delta_stats(sub)
        p_str = f"{res['p']:.3f}" if res["p"] >= 0.001 else "<.001"
        print(f"  {orth:<30}: omit={res['omit_rate']:.1%}, d={res['cohen_d']:.3f}, p={p_str}")

    print_subsection("NYE2026 omission rate by model")
    for model in long["model"].unique():
        sub = long[(long["segment"] == "NYE2026") & (long["model"] == model)]
        print(f"  {model:<25}: {sub['is_omitted'].mean():.1%}")

    print_subsection("Will you brie mine? (appropriate omission / untranslatable pun)")
    brie = long[long["segment"].str.contains("brie", case=False, na=False)]
    res = quality_delta_stats(brie, "Will you brie mine?")
    p_str = f"{res['p']:.3f}"
    print(f"  Omission rate: {res['omit_rate']:.1%}")
    print(f"  Overall quality (translated): {res['overall_trans']:.2f}")
    print(f"  Overall quality (omitted):    {res['overall_omit']:.2f}")
    print(f"  Delta: {res['delta']:.3f}, d = {res['cohen_d']:.3f}, p = {p_str}")
    print(f"  Interpretation: negative delta = omission associated with better "
          f"email quality; untranslatable content.")

    print_subsection("Brie mine omission by writing system")
    for orth in long["orthography"].dropna().unique():
        sub = brie[brie["orthography"] == orth]
        if sub.empty or sub["is_omitted"].sum() < 2:
            continue
        res = quality_delta_stats(sub)
        p_str = f"{res['p']:.3f}" if res["p"] >= 0.001 else "<.001"
        print(f"  {orth:<30}: omit={res['omit_rate']:.1%}, d={res['cohen_d']:.3f}, p={p_str}")

    print_subsection("Top failure-omission segments (largest positive quality delta)")
    results = []
    for seg in long["segment"].dropna().unique():
        sub = long[long["segment"] == seg]
        if sub["is_omitted"].sum() < 5:
            continue
        res = quality_delta_stats(sub, seg)
        results.append(res)
    results.sort(key=lambda x: x["cohen_d"], reverse=True)
    print(f"  {'Segment':<35} {'Category':<22} {'d':>7} {'Delta':>7} {'Omit%':>7}")
    print("  " + "-" * 85)
    for r in results[:10]:
        seg = r["label"]
        cat = long[long["segment"] == seg]["segment_category"].iloc[0] if not long[long["segment"] == seg].empty else ""
        print(f"  {seg:<35} {cat:<22} {r['cohen_d']:>7.3f} "
              f"{r['delta']:>7.3f} {r['omit_rate']:>6.1%}")


def writing_system_effects(long: pd.DataFrame) -> None:
    """Section 4.5: Writing system and morphological effects."""
    print_section("SECTION 4.5: WRITING SYSTEM AND MORPHOLOGICAL EFFECTS")

    print_subsection("Omission rate by writing system × category")
    orths = long["orthography"].dropna().unique()
    cats  = ["cultural concepts", "holidays", "idioms", "puns"]
    print(f"  {'Orthography':<30} " + "  ".join(f"{c[:8]:>9}" for c in cats))
    print("  " + "-" * 75)
    for orth in sorted(orths):
        rates = []
        for cat in cats:
            sub = long[(long["orthography"] == orth) & (long["segment_category"] == cat)]
            rates.append(f"{sub['is_omitted'].mean():>8.1%}" if not sub.empty else "       —")
        print(f"  {orth:<30} {'  '.join(rates)}")

    print_subsection("Quality delta by writing system (overall omission)")
    print(f"  {'Orthography':<30} {'OvQ(trans)':>11} {'OvQ(omit)':>10} "
          f"{'Delta':>7} {'d':>7} {'p':>9}")
    print("  " + "-" * 80)
    for orth in sorted(orths):
        sub = long[long["orthography"] == orth]
        if sub["is_omitted"].sum() < 5:
            continue
        res = quality_delta_stats(sub)
        p_str = f"{res['p']:.3f}" if res["p"] >= 0.001 else "<.001"
        print(f"  {orth:<30} {res['overall_trans']:>11.2f} {res['overall_omit']:>10.2f} "
              f"{res['delta']:>7.3f} {res['cohen_d']:>7.3f} {p_str:>9}")

    print_subsection("Morphological type effects")
    morphology_map = {
        "Afrikaans":           "Fusional",
        "Arabic":              "Fusional",
        "Brazilian Portuguese":"Fusional",
        "Czech":               "Fusional",
        "Dutch":               "Fusional",
        "Hebrew":              "Fusional",
        "Hindi":               "Fusional",
        "Russian":             "Fusional",
        "Spanish":             "Fusional",
        "Urdu":                "Fusional",
        "Japanese":            "Agglutinative",
        "Korean":              "Agglutinative",
        "Swahili":             "Agglutinative",
        "Cantonese":           "Isolating",
        "Mandarin":            "Isolating",
    }
    long["morphology"] = long["language"].map(morphology_map)

    print(f"  {'Morphology':<16} {'Languages':<55} {'Delta':>7} {'d':>7} {'p':>9}")
    print("  " + "-" * 96)
    for morph in ["Fusional", "Agglutinative", "Isolating"]:
        sub = long[long["morphology"] == morph]
        langs = ", ".join(sorted(sub["language"].unique()))
        res = quality_delta_stats(sub)
        p_str = f"{res['p']:.3f}" if res["p"] >= 0.001 else "<.001"
        print(f"  {morph:<16} {langs:<55} {res['delta']:>7.3f} "
              f"{res['cohen_d']:>7.3f} {p_str:>9}")

    print_subsection("Korean outlier within Agglutinative group")
    for lang in ["Japanese", "Korean", "Swahili"]:
        sub = long[long["language"] == lang]
        res = quality_delta_stats(sub, lang)
        p_str = f"{res['p']:.3f}" if res["p"] >= 0.001 else "<.001"
        print(f"  {lang}: omit={res['omit_rate']:.1%}, delta={res['delta']:.3f}, "
              f"d={res['cohen_d']:.3f}, p={p_str}")


def irr_summary() -> None:
    """Report IRR values from parent paper [4]."""
    print_section("INTER-RATER RELIABILITY (from parent paper [4], Table C8)")
    print("  IRR was assessed in [4] using Krippendorff's alpha (ordinal) and")
    print("  Gwet's AC2 with quadratic weights. NA (omitted segment) ratings")
    print("  were excluded from all calculations.")
    print(f"\n  Overall (all segments):  alpha = {REPORTED_IRR['overall_segment']['krippendorff_alpha']}, "
          f"AC2 = {REPORTED_IRR['overall_segment']['gwet_ac2']}")
    print("\n  By category:")
    for cat, vals in REPORTED_IRR["by_category"].items():
        print(f"    {cat:<22}: alpha = {vals['krippendorff_alpha']}, AC2 = {vals['gwet_ac2']}")
    print("\n  Note on idioms: AC2 (0.107) substantially lower than alpha (0.405),")
    print("  indicating high observed agreement driven by prevalence of low ratings")
    print("  rather than genuine rater consensus.")


def clmm_summary() -> None:
    """Report key CLMM estimates from parent paper [4]."""
    print_section("CLMM KEY ESTIMATES (from parent paper [4], Table C1)")
    print("  Cumulative link mixed model (logit link), ordinal package in R.")
    print("  Fixed effects: model, language, segment category (+ interactions).")
    print("  Random intercepts: annotator (SD=0.70), segment (SD=1.76).")
    print("  logLik = -14411.63, AIC = 28965.26, n = 13125.")
    print("  Reference levels: GPT-5 (model), Afrikaans (language).")
    print()
    for key, vals in CLMM_ESTIMATES.items():
        if isinstance(vals, dict):
            print(f"  {key:<30}: beta = {vals['beta']:>5}, SE = {vals['se']}, p {vals['p']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    DATA_PATH = "Bombadil_Expansion_Data_-_clean.xlsx"

    print("Loading data...")
    long = load_data(DATA_PATH)
    print(f"Loaded {len(long)} segment-level annotations "
          f"({long['is_omitted'].sum()} omitted, "
          f"{(~long['is_omitted']).sum()} rated).")

    verify_against_paper(long)
    irr_summary()
    clmm_summary()
    table1_category_omission(long)
    table2_segment_omission(long)
    model_level_effects(long)
    appropriate_vs_failure_omission(long)
    writing_system_effects(long)

    print("\n" + "=" * 70)
    print("  Analysis complete.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
