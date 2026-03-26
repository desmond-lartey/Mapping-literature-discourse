# Governing with Artificial Intelligence
### Mapping the Knowledge Systems Shaping Urban Intelligence

**Desmond Lartey · Kris M.Y. Law**  
*Technology in Society* 86 (2026) 103321  
DOI: [10.1016/j.techsoc.2026.103321](https://doi.org/10.1016/j.techsoc.2026.103321)

---

## What this repository contains

This repository holds the analysis code used to produce all quantitative results and figures in the paper. The study maps the cognitive structure of AI urbanism by applying natural language processing, dimensionality reduction, and network visualisation to a corpus of 5,634 scholarly articles on AI in urban governance.

Running the script reproduces:

- Semantic classification of articles across 12 conceptual categories and 3 knowledge lenses
- A weighted lens matrix and temporal trend dataset
- A stratified validation sample for manual coding
- Figures 2 through 6 from the paper

---

## Background

Cities are increasingly governed through AI systems: predictive models, digital twins, welfare allocation algorithms, and autonomous infrastructure. This study treats that discourse as a structured knowledge system and asks what conceptual logics are embedded in it.

The analysis identifies three foundational lenses that organise the literature:

| Lens | What it captures |
|------|-----------------|
| Key Stakeholders and Entities | Technologies, platforms, institutions, and infrastructure enabling AI in cities |
| Models of Interaction | Feedback dynamics, decision-making, human-machine co-agency |
| External Influencing Factors | Governance, ethics, regulation, cultural context, sustainability |

These lenses are synthesised into a systems-based governance framework linking them to 12 urban subsystems (e.g. platform governance, ethical standards, public legitimacy).

---

## Repository structure

```
├── analysis.py          Main analysis script (this is the file to run)
├── requirements.txt     Python package dependencies
├── data/                Place your input files here
│   ├── Merged_Tagged_AIUrbanism.xlsx
│   ├── Hybrid_Conceptual_Lens_Weighted_Matrix.xlsx
│   └── Hybrid_Conceptual_Lens_Weighted_Matrix_trend_contributing_Analysis.xlsx
└── output/              All figures and result files are written here (auto-created)
```

---

## Input files

| File | Description |
|------|-------------|
| `Merged_Tagged_AIUrbanism.xlsx` | Master article database. Each row is one article with columns: Title, Abstract, Keyword, Year, SearchIndicator, ConceptualLens |
| `Hybrid_Conceptual_Lens_Weighted_Matrix.xlsx` | Lens weight scores per search indicator (rows = indicators, columns = lenses) |
| `Hybrid_Conceptual_Lens_Weighted_Matrix_trend_contributing_Analysis.xlsx` | Yearly lens contribution totals (rows = years, columns = lenses) |

Place all three files in the `data/` folder before running.

---

## Output files

| File | Corresponds to |
|------|---------------|
| `Tagged_AIUrbanism.xlsx` | Master database with automated lens assignments added |
| `Weighted_Matrix.xlsx` | Pivot of article counts by indicator and lens |
| `Trend_Matrix.xlsx` | Article counts aggregated by year and lens |
| `Validation_Sample.xlsx` | Stratified 10% sample for manual inter-rater coding |
| `figure2_indicator_trends.png` | Figure 2 — Trends and growth dynamics of search indicators |
| `figure3_heatmap_network.png` | Figure 3 — Semantic mapping of lenses |
| `figure4_temporal_lowess.png` | Figure 4 — LOWESS-smoothed lens trajectories |
| `figure5_ordination.png` | Figure 5 — PCA, NMDS, and GNMDS ordination |
| `figure6_governance_framework.png` | Figure 6 — Systems-based governance framework |

---

## How to run

### 1. Clone the repository

```bash
git clone https://github.com/desmond-lartey/Mapping-literature-discourse.git
cd Mapping-literature-discourse
```

### 2. Install dependencies

Python 3.9 or later is recommended.

```bash
pip install -r requirements.txt
```

### 3. Add your data

Copy the three input files into the `data/` folder.

### 4. Run the analysis

```bash
python analysis.py
```

The script works through the following steps in sequence:

1. Assigns each article a conceptual lens using a hybrid approach (keyword matching + sentence transformer)
2. Builds the weighted lens matrix
3. Builds the yearly trend matrix
4. Creates a validation sample for manual coding
5. Generates all figures

Progress messages are printed at each step. The full pipeline takes a few minutes on a standard laptop, mostly due to the sentence transformer encoding step.

---

## Running individual steps

Each step is a standalone function. You can import and call them individually in a notebook or script:

```python
from analysis import (
    tag_articles_with_lens,
    build_weighted_matrix,
    figure4_temporal_evolution,
    figure6_governance_network,
)

# Run only the temporal figure using the built-in data
figure4_temporal_evolution()

# Run only the governance network figure
figure6_governance_network()

# Tag your own article database
tag_articles_with_lens("data/MyArticles.xlsx", "output/Tagged.xlsx")
```

Figures 3, 4, and 6 use data tables embedded directly in the script (matching the paper values), so they run without any input files. Figures 2 and 5 require the input files.

---

## Validation

The script generates a `Validation_Sample.xlsx` file with a stratified 10% sample of articles (roughly 563 rows). A human coder fills in the `Manual_Lens` column using the same three lens options. To compute agreement statistics once coding is complete:

```python
from analysis import compute_validation_scores
compute_validation_scores("output/Validation_Sample.xlsx")
```

This prints exact agreement, Cohen's kappa, a classification report, and a confusion matrix. The paper reports 95.74% exact agreement and kappa = 0.933 on this validation subset.

---

## Classification approach

Articles are classified in two stages:

**Stage 1 — Keyword matching.** Each article already carries a `SearchIndicator` column (Technology, Governance, Agency, etc.) from the original search strategy. A fixed lookup table maps each indicator to its primary lens (Table 2 in the paper).

**Stage 2 — Semantic similarity.** The article text (title + abstract + keywords) is encoded using the `all-MiniLM-L6-v2` sentence transformer. Cosine similarity is computed against short natural-language descriptions of each lens. Articles with no keyword match, or with a match below the 0.45 similarity threshold, fall back to the highest-scoring semantic match.

The two signals are combined in a simple ensemble: the keyword-based assignment wins when available; the semantic signal fills gaps.

---

## Ordination methods

The script implements three ordination methods to validate the lens structure:

| Method | Purpose |
|--------|---------|
| PCA | Projects temporal lens trajectories into a reduced two-dimensional space to reveal directional change over time |
| NMDS | Non-metric multidimensional scaling positions each search indicator in semantic space according to its lens weight profile |
| GNMDS | Metric MDS provides an observer-independent baseline for comparing indicator relationships |

Statistical validation (PERMANOVA, F > 25, p < 0.001) confirmed that between-lens variance significantly exceeds within-lens variance, supporting the three-lens structure.

---

## Citation

If you use this code in your own work, please cite the paper:

```bibtex
@article{lartey2026governing,
  title   = {Governing with artificial intelligence: Mapping the knowledge systems
             shaping urban intelligence},
  author  = {Lartey, Desmond and Law, Kris M.Y.},
  journal = {Technology in Society},
  volume  = {86},
  pages   = {103321},
  year    = {2026},
  doi     = {10.1016/j.techsoc.2026.103321}
}
```

---

## Contact

Questions about the code or data can be directed to **Desmond Lartey** at larteydesmond3@gmail.com.
