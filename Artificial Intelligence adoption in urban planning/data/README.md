# Data

**Your corpus goes here.**

The dataset behind the published paper is our own collected material and is not
distributed with this repository. The notebooks run on any corpus matching the
structure below, so you can apply the same method to your own literature search.

## What goes where

```
data/
├── raw_ris/       your .ris exports          -> input to notebook 01
├── raw_csv/       your .csv exports          -> input to notebook 01
├── vosviewer/     VOSviewer JSON export      -> input to notebook 04
├── reference/     countries.csv (ships with the repo)
├── interim/       intermediate files from notebook 01 (gitignored)
└── corpus.csv     the handover file (gitignored - derived, not source)
```

## Three ways to get a corpus

### 1. Build one from database exports

Drop `.ris` files in `raw_ris/` and `.csv` files in `raw_csv/`, then run
`notebooks/01_corpus_assembly.ipynb`. It parses both formats, normalises the columns,
deduplicates on DOI then title, applies the screening rules, and writes `corpus.csv`.

Scopus, Web of Science and ScienceDirect CSV headers are mapped automatically. If your
database uses different names, add them to `CSV_ALIASES` in Stage A1.

### 2. Bring your own table

If your literature is already in a spreadsheet, rename the columns to match the schema
below and save it as `corpus.csv` here. Notebooks 02–04 validate on load and report
precisely what is wrong rather than failing several stages later.

### 3. Not at all

Notebook 01 generates a small synthetic corpus if it finds no exports, and notebook 04
generates a synthetic network if it finds no VOSviewer JSON. Both are for reading and
testing the pipeline, not for producing results, output built this way is stamped
**DEMO DATA** or **SYNTHETIC NETWORK**.

## Schema

`corpus.csv`, one row per record:

| Column | Required | Notes |
|---|---|---|
| `Title` | yes | |
| `Abstract` | yes | may be empty on some rows |
| `Keyword` | yes | semicolon separated |
| `Year` | yes | integer, 1900–2100 |
| `Journal` | yes | used for discipline classification in notebook 02 |
| `Affiliation` | no | **worth chasing down**, see below |
| `DOI` | no | bare identifier, no `https://doi.org/` prefix |
| `Authors` | no | semicolon separated |
| `StudyType` | no | populates Figure 3c |
| `SourceFile` | no | provenance |

### On affiliations

Without `Affiliation`, notebook 03 can tell you what the literature is **about** but not
where its authors are **based**. For a review whose findings concern geographic
representation those are different claims, and the gap between them is often the more
interesting result. Most databases include affiliations if you ask for them at export
time. It is worth re-exporting to get them.

### On StudyType

The paper's Figure 3c reports literature reviews (283), systematic reviews (180),
non-RCT observational studies (67) and meta-analyses (58). These come from full-text
screening, not from metadata, so no script can infer them. Add the column during
screening and notebook 02 will draw the panel; otherwise it says so and moves on.

## Reference table

`reference/countries.csv` ships with the repo: 187 countries with centroid coordinates,
region, and a pipe-separated alias list holding demonyms and major cities.

| Region | Countries |
|---|---|
| Africa | 54 |
| Asia | 48 |
| Europe | 41 |
| Caribbean | 14 |
| South America | 12 |
| Oceania | 8 |
| Central America | 7 |
| North America | 3 |

Edit it freely, add a city your corpus mentions often, or a name variant your database
uses. A country absent from this table cannot be found by the geocoder, and a country
that is never found reads as a region that does not publish, so coverage here directly
shapes what notebook 03 can conclude. Stage C1 prints the coverage before producing any
result.

## VOSviewer network

Notebook 04 reads a VOSviewer JSON export from `vosviewer/`. To produce one:

1. Build your keyword co-occurrence map in VOSviewer.
2. **File → Save → VOSviewer JSON file**.
3. Save it as `data/vosviewer/VOSviewer-network.json`.

The loader reads whatever weight and score attributes the export contains rather than
assuming `Occurrences` and `Avg. pub. year`, so co-authorship and co-citation maps work
too.
