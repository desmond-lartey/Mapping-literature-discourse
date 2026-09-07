[![GitHub Badge](https://img.shields.io/github/followers/desmond-lartey?style=social)](https://github.com/desmond-lartey)
[![Publications Badge](https://img.shields.io/badge/Google-Scholar-lightgrey)](https://scholar.google.com/citations?user=NJuroh8AAAAJ&hl=en)
[![LinkedIn Badge](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/desmond-lartey/)
[![DOI](https://img.shields.io/badge/DOI-10.1016%2Fj.techsoc.2026.103321-blue)](https://doi.org/10.1016/j.techsoc.2026.103321)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

# Governing with Artificial Intelligence
### Mapping the Knowledge Systems Shaping Urban Intelligence

**Desmond Lartey · Kris M.Y. Law**
*Technology in Society* **86** (2026) 103321
DOI: [10.1016/j.techsoc.2026.103321](https://doi.org/10.1016/j.techsoc.2026.103321)

---

## What this repository is

The analysis pipeline behind the paper, written so that **you can run it on your own
literature corpus**.

The study maps the cognitive structure of AI urbanism by classifying scholarly
literature across 12 conceptual categories, reducing them to 3 knowledge lenses, and
tracing how those lenses interact across 12 urban governance subsystems. The method is
general: it works on any body of literature you can export from Scopus, ScienceDirect
or a comparable database.

Two notebooks, run in order:

| Notebook | Takes | Produces |
|---|---|---|
| `01_corpus_assembly.ipynb` | your `.ris` exports | `data/corpus.csv` |
| `02_cognitive_analysis.ipynb` | `data/corpus.csv` | classified corpus, matrices, statistics, Figures 2–6 |

---

## Quick start

```bash
git clone https://github.com/desmond-lartey/Mapping-literature-discourse.git
cd Mapping-literature-discourse
pip install -r requirements.txt
jupyter lab notebooks/02_cognitive_analysis.ipynb
```

Run all cells. It works immediately with no data files and no model download: by
default it generates a small synthetic corpus so you can see the whole pipeline
execute and inspect what each stage produces before committing your own data to it.
Figures produced this way are stamped **DEMO DATA** so they are never mistaken for
results.

When you are ready to use your own corpus:

1. Put your `.ris` exports in `data/raw_ris/` and run `01_corpus_assembly.ipynb`
   (or write `data/corpus.csv` yourself — the schema is in [`data/README.md`](data/README.md)).
2. In `02_cognitive_analysis.ipynb`, Stage 0: set `CONFIG["data_mode"] = "real"`.
3. Run all cells.

---

## Bring your own data

**The corpus used in the published paper is not distributed here.** It is our own
collected dataset. This repository provides the method, not the material.

What you need is a `corpus.csv` with one row per article and these columns:

| Column | Required | Type | Notes |
|---|---|---|---|
| `Title` | yes | text | |
| `Abstract` | yes | text | may be blank for some rows |
| `Keyword` | yes | text | semicolon separated |
| `Year` | yes | integer | 1900–2100 |
| `SearchIndicator` | yes | text | one of the 12 categories below |
| `DOI` | no | text | bare identifier |
| `Authors`, `Journal`, `SourceFile` | no | text | carried through if present |

The 12 categories: `Action`, `Agency`, `Culture`, `Data`, `Governance`, `Materiality`,
`Personality`, `Security`, `Space`, `Sustainability`, `Technology`, `Time`.

Notebook 01 builds this for you from RIS exports. If you already have your literature
in a spreadsheet, rename the columns to match and drop it in as
`data/corpus.csv` — Stage 2 validates the file and tells you exactly what is wrong
rather than failing several stages later with an unrelated error.

Sample `.ris` files are included in `data/raw_ris/` so you can watch the parser and
screening funnel work. They are format examples on unrelated topics, not the study
corpus.

### Adapting the framework

The 12 categories and 3 lenses are defined in **Stage 1** of notebook 02, in plain
dictionaries. If your field organises differently, edit them there and everything
downstream — matrices, ordination, statistics, all five figures — follows
automatically. Nothing is hard-coded further down.

---

## The analysis, stage by stage

Notebook 02 runs in ten numbered stages. Each states what it does, prints what it
produced so you can check it before moving on, and saves a checkpoint to
`outputs/checkpoints/`.

| Stage | Does | Paper |
|---|---|---|
| 0 | Setup, seeds, one `CONFIG` block controlling every choice | — |
| 1 | The 12 categories, 3 lenses, published reference values | Table 2 |
| 2 | Load and validate the corpus | §3.1 |
| 3 | Semantic scoring against the lens descriptions | §3.1.2 |
| 4 | Ensemble lens assignment, plus a sensitivity grid | §3.1.3 |
| 5 | Weighted matrix and temporal trend matrix | §3.2.1 |
| 6 | Validation sample, Cohen's κ with a bootstrap CI | §3.1.3 |
| 7 | PCA, NMDS, GNMDS, Kruskal stress | §3.2.2 |
| 8 | PERMANOVA at indicator and article level | §3.2.2 |
| 9 | Figures 2–6 | §4 |
| 10 | Reproducibility manifest with output checksums | — |

Because of the checkpoints you do not have to run top to bottom. Run Stages 0–1, which
are cheap, then jump to whichever stage you want and run its resume cell first.

### Outputs

```
outputs/
├── figures/        figure2 ... figure6, PNG at the DPI set in CONFIG
├── tables/         validation coder workbook
├── checkpoints/    every stage result, as CSV or JSON
└── reproducibility_report.json
```

The manifest records the configuration, package versions, platform, every headline
statistic, and a SHA-256 for each output file, so two runs can be compared directly.

---

## Notes on the method

A few choices in the code are worth knowing about before you adapt it.

**The weighted matrix is a semantic mass, not an article count.** Because each
category maps to exactly one lens a priori, counting articles per category per lens
gives a diagonal matrix, and ordination on a diagonal matrix simply recovers the
lookup table. The matrix is therefore built from the average share of similarity each
category's articles place on each lens. Stage 5 prints the count pivot alongside it so
the difference is visible.

**The keyword and semantic signals are separately weighted.** The ensemble scores each
lens as `keyword_weight · 1{category → lens} + semantic_weight · share[lens]`. With
`keyword_weight ≥ 1` the assignment is effectively a lookup driven by
`SearchIndicator`; set it to `0` for a purely semantic assignment. Stage 4 runs both
across a grid so you can see how far the two agree on your data.

**PERMANOVA is reported at two units.** Twelve categories in three groups has little
statistical power and returns F values around 1–3 even when the grouping is sound;
the article-level test over thousands of records returns F in the tens or hundreds.
Stage 8 runs both. Report n, unit and distance measure alongside any F you quote.

**Two dependencies are optional.** `sentence-transformers` is the paper's semantic
backend and needs a ~90 MB download; without it the notebook uses TF-IDF cosine, which
is offline and deterministic but an approximation. `statsmodels` provides LOWESS for
Figure 4; without it a local linear fallback is used. Both fall back silently and
print which path they took.

---

## Requirements

Python 3.9 or later.

```bash
pip install -r requirements.txt
```

Everything runs on CPU. No GPU is needed at any stage.

---

## Citation

```bibtex
@article{lartey2026governing,
  title   = {Governing with artificial intelligence: Mapping the knowledge
             systems shaping urban intelligence},
  author  = {Lartey, Desmond and Law, Kris M. Y.},
  journal = {Technology in Society},
  volume  = {86},
  pages   = {103321},
  year    = {2026},
  doi     = {10.1016/j.techsoc.2026.103321}
}
```

## Contact

**Desmond Lartey** — larteydesmond3@gmail.com

## License

MIT. See [LICENSE](LICENSE).
