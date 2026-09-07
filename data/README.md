# Data

**Your corpus goes here.**

The dataset behind the published paper is our own collected material and is not
distributed with this repository. The notebooks are written to run on any corpus that
matches the structure below, so you can apply the same method to your own literature
search.

## Two ways to get a corpus

### 1. Build one from RIS exports

Put your `.ris` files in `raw_ris/` and run `notebooks/01_corpus_assembly.ipynb`. It
parses, normalises, deduplicates, tags and screens them, and writes `corpus.csv` here.

Name each export after its search category - `Technology_1.ris`, `Governance_2a.ris` -
and Stage A4 reads the category straight off the filename. Otherwise it falls back to
matching the Table 1 search terms against each record's text, which works but is less
exact.

### 2. Bring your own table

If your literature is already in a spreadsheet, rename the columns to match the schema
below and save it as `corpus.csv` in this folder. Stage 2 of the analysis notebook
validates it on load and reports precisely what is wrong, so a schema problem surfaces
immediately rather than four stages later.

You can also skip both and leave `CONFIG["data_mode"] = "demo"` in the analysis
notebook, which generates a small synthetic corpus. That is for reading and testing
the pipeline, not for producing results - figures made this way are stamped
**DEMO DATA**.

## Schema

`corpus.csv`, one row per article:

| Column | Required | Type | Notes |
|---|---|---|---|
| `Title` | yes | text | |
| `Abstract` | yes | text | may be empty for some rows |
| `Keyword` | yes | text | semicolon separated |
| `Year` | yes | integer | 1900–2100 |
| `SearchIndicator` | yes | text | one of the 12 names below |
| `DOI` | no | text | bare identifier, no `https://doi.org/` prefix |
| `Authors` | no | text | semicolon separated |
| `Journal` | no | text | |
| `SourceFile` | no | text | provenance |

The 12 categories: `Action`, `Agency`, `Culture`, `Data`, `Governance`, `Materiality`,
`Personality`, `Security`, `Space`, `Sustainability`, `Technology`, `Time`.

Using different categories is fine - edit the definitions in Stage 1 of the analysis
notebook and everything downstream adapts.

## Folder contents

```
data/
├── raw_ris/     your RIS exports, input to notebook 01
├── interim/     intermediate files written by notebook 01 (gitignored)
└── corpus.csv   the handover file (gitignored - it is derived, not source)
```

The `.ris` files currently in `raw_ris/` are **format samples**: real exports, but on
unrelated topics. They let you watch the parser and the screening funnel run before
you commit your own search to it. Replace them with your own.

## Optional: validation

If you hand-code a sample to check the automated classification, save the completed
sheet as `validation_completed.csv` here. Stage 6 of the analysis notebook will find
it and report exact agreement, Cohen's κ with a bootstrap confidence interval, a
per-lens classification report and a confusion matrix. The blank coder workbook is
generated for you in `outputs/tables/`.
