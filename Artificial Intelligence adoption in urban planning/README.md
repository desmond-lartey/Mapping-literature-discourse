[![GitHub Badge](https://img.shields.io/github/followers/desmond-lartey?style=social)](https://github.com/desmond-lartey)
[![Publications Badge](https://img.shields.io/badge/Google-Scholar-lightgrey)](https://scholar.google.com/citations?user=NJuroh8AAAAJ&hl=en)
[![DOI](https://img.shields.io/badge/DOI-10.1016%2Fj.landurbplan.2025.105337-blue)](https://doi.org/10.1016/j.landurbplan.2025.105337)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

# AI Adoption in Urban Planning Governance
### A systematic review of advancements in decision-making and policy making

**Desmond Lartey · Kris M.Y. Law**
*Landscape and Urban Planning* **258** (2025) 105337
DOI: [10.1016/j.landurbplan.2025.105337](https://doi.org/10.1016/j.landurbplan.2025.105337)

---

## What this repository is

The analysis pipeline behind the paper, written so that **you can run it on your own
literature corpus**.

The study reviewed 3,715 retrieved records down to 588 included studies across 83
countries, then analysed them four ways: bibliometric trends, geographic distribution,
keyword co-occurrence networks, and a thematic integration matrix. The method is
general, it works on any body of literature you can export from PubMed, Scopus,
ScienceDirect or a comparable database.

Four notebooks, run in order:

| Notebook | Takes | Produces | Paper |
|---|---|---|---|
| `01_corpus_assembly.ipynb` | `.ris` / `.csv` exports | `data/corpus.csv` | §3.1 |
| `02_bibliometric_analysis.ipynb` | `corpus.csv` | Figures 3, 5a–b | §4.2, §4.4 |
| `03_geographic_mapping.ipynb` | `corpus.csv` | Figure 2, country tables | §3.2.2, §4.1 |
| `04_network_and_matrix.ipynb` | `corpus.csv` + VOSviewer JSON | Figure 4, Table 1, Figure 5c | §3.2.3–4, §4.3 |

---

## Quick start

```bash
git clone https://github.com/desmond-lartey/AI-adoption-urban-planning.git
cd AI-adoption-urban-planning
pip install -r requirements.txt
jupyter lab notebooks/01_corpus_assembly.ipynb
```

Run all cells in each notebook in order. Everything works immediately with no data
files: notebook 01 generates a synthetic corpus if it finds no exports, and notebook 04
generates a synthetic network if it finds no VOSviewer JSON. Output built this way is
stamped **DEMO DATA** or **SYNTHETIC NETWORK** so it can never be mistaken for a result.

To use your own material, see below.

---

## Bring your own data

**The corpus behind the published paper is not distributed here.** It is our own
collected dataset. This repository provides the method, not the material.

### Literature corpus

Put `.ris` exports in `data/raw_ris/` and `.csv` exports in `data/raw_csv/`, then run
notebook 01. It parses, normalises, deduplicates, screens and exports `data/corpus.csv`.

If your literature is already in a spreadsheet, rename the columns to match and save it
as `data/corpus.csv` directly. The required columns are `Title`, `Abstract`, `Keyword`,
`Year` and `Journal`; `Affiliation`, `DOI` and `StudyType` are optional but each unlocks
something (see [`data/README.md`](data/README.md)).

### Keyword network

Notebook 04 reads a VOSviewer JSON export from `data/vosviewer/`. Build your
co-occurrence map in VOSviewer, then **File → Save → VOSviewer JSON file**.

### Search strategy used in the paper

Applied to PubMed, ScienceDirect and Consensus:

```
((((decision making) AND (urban planning)) AND (policy making)) AND (Artificial Intelligence))
```

ScienceDirect was filtered to review and research articles, 2004–2024, in Social
Sciences, Environmental Science and Decision Sciences. Snowballing on reference lists
supplemented the search.

### Adapting the framework

The extraction keywords, application areas, disciplines and matrix themes are plain
dictionaries at the top of each notebook. Edit them and everything downstream,
classifications, figures, tables, comparisons, follows automatically. Nothing is
hard-coded further down.

---

## Comparing against the paper

Each notebook holds the published values as **comparison targets**, never as figure
input. Every figure is computed from whatever corpus you load; the paper's numbers are
used only to score how closely your run tracks it.

| Published | Where | Notebook |
|---|---|---|
| 3,715 retrieved → 588 included | §3.1.3 | 01 |
| 588 studies, 83 countries | §4.1 | 03 |
| Regional totals: Europe 187, Asia 149, N. America 143, S. America 40, Africa 35, Oceania 19, C. America 15 | Fig. 2 | 03 |
| Keyword share: AI ~69%, decision-making ~22% | Fig. 3a | 02 |
| Study types: lit. review 283, systematic review 180 | Fig. 3c | 02 |
| Application areas: Community & Social Services 278, Environmental Planning 148 | Fig. 5a | 02 |
| Disciplines: Public Administration 249, Social Sciences 234 | Fig. 5b | 02 |
| 26 keyword clusters | Table 1 | 04 |
| Practical integration matrix | Fig. 5c | 04 |

---

## Notes on the method

Four choices worth knowing about before adapting the code.

**Geocoding is offline and covers the whole world.** Notebook 03 matches against
`data/reference/countries.csv`, 187 countries with centroids, regions, demonyms and
major cities. Coverage is deliberately complete for **all 54 African countries and all
7 Central American ones**, since a country missing from a reference table cannot be
found, and a country that is never found reads as a region that does not publish. The
notebook prints coverage by region before producing any result so you can confirm this
yourself. Matching is longest-first, so *South Africa* beats *Africa* and *United Arab
Emirates* beats *United*; a few bare names are excluded as too ambiguous (*Georgia* is
matched only via *Tbilisi*, being far more often the US state in this literature).

**"About" and "from" are kept separate.** Study countries come from title, abstract and
keywords; author countries come from affiliations. A review can be *about* Nairobi and
written entirely in Europe, collapsing those into one number turns a claim about
research capacity into a claim about research attention. Notebook 03 reports both and
the gap between them.

**Journal names are not used as location evidence.** *Journal of the American Planning
Association* would tag every paper it publishes as United States regardless of where the
study was done. Journal is used for discipline classification in notebook 02 and
deliberately excluded from the geographic analysis.

**Every country mentioned is counted, not just the first.** A paper comparing Accra and
Nairobi is evidence for both. Records with no detectable location are counted and
reported rather than dropped, so you can see how much of the corpus a geographic claim
actually rests on.

---

## Outputs

```
outputs/
├── figures/     figure2 … figure5c, PNG at the DPI set in CONFIG
├── tables/      every underlying table as CSV
└── run_report.json
```

The run report records the corpus size, network size, whether either was synthetic,
package versions and a SHA-256 for each output, so two runs can be compared directly.

---

## Citation

```bibtex
@article{lartey2025ai,
  title   = {Artificial intelligence adoption in urban planning governance:
             A systematic review of advancements in decision-making,
             and policy making},
  author  = {Lartey, Desmond and Law, Kris M. Y.},
  journal = {Landscape and Urban Planning},
  volume  = {258},
  pages   = {105337},
  year    = {2025},
  doi     = {10.1016/j.landurbplan.2025.105337}
}
```

## Related work

Companion paper: [Governing with artificial intelligence: Mapping the knowledge systems
shaping urban intelligence](https://github.com/desmond-lartey/Mapping-literature-discourse),
*Technology in Society* 86 (2026) 103321.

Part of the PhD thesis repository:
[Knowledge-Management-Informatics](https://github.com/desmond-lartey/Knowledge-Management-Informatics).

## Contact

**Desmond Lartey**, larteydesmond3@gmail.com

## License

MIT. See [LICENSE](LICENSE).
