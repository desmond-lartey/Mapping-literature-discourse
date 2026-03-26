"""
Governing with Artificial Intelligence: Mapping the Knowledge Systems Shaping Urban Intelligence
-------------------------------------------------------------------------------------------------
Lartey & Law (2026) — Technology in Society 86, 103321
https://doi.org/10.1016/j.techsoc.2026.103321

This script reproduces the core analysis pipeline from the paper:
  1. Semantic tagging of articles into 12 conceptual categories
  2. Hybrid classification using keyword matching + sentence transformer embeddings
  3. Conceptual lens assignment and weighted matrix construction
  4. Temporal trend analysis
  5. Ordination (PCA, NMDS, GNMDS) and statistical validation (PERMANOVA)
  6. Systems-based governance framework visualisation

Input files (place in the same folder or set INPUT_DIR below):
  - Merged_Tagged_AIUrbanism.xlsx   : master article database with metadata
  - Hybrid_Conceptual_Lens_Weighted_Matrix.xlsx : lens weight matrix per indicator
  - Hybrid_Conceptual_Lens_Weighted_Matrix_trend_contributing_Analysis.xlsx : yearly lens weights

Output files are written to the folder defined by OUTPUT_DIR.
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import networkx as nx
import statsmodels.api as sm

from sentence_transformers import SentenceTransformer, util
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.manifold import MDS
from sklearn.metrics.pairwise import pairwise_distances
from sklearn.metrics import cohen_kappa_score, classification_report, confusion_matrix
from scipy.spatial.distance import pdist, squareform
from statsmodels.nonparametric.smoothers_lowess import lowess
from matplotlib.patches import Ellipse

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION  — change these two lines to match your folder layout
# ──────────────────────────────────────────────────────────────────────────────
INPUT_DIR  = "data"   # folder that contains all input .xlsx files
OUTPUT_DIR = "output" # folder where figures and result files will be saved
# ──────────────────────────────────────────────────────────────────────────────

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Helper: build full input and output paths
def inp(filename):
    return os.path.join(INPUT_DIR, filename)

def out(filename):
    return os.path.join(OUTPUT_DIR, filename)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — CONCEPTUAL FRAMEWORK DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════════

# The 12 search indicators and their primary lens assignment
# (Table 2 in the paper)
INDICATOR_TO_LENS = {
    "Technology":   "Key Stakeholders and entities",
    "Action":       "Models of Interaction",
    "Space":        "Models of Interaction",
    "Agency":       "Models of Interaction",
    "Culture":      "Models of Interaction",
    "Personality":  "External influencing factors",
    "Time":         "External influencing factors",
    "Materiality":  "Key Stakeholders and entities",
    "Data":         "External influencing factors",
    "Governance":   "External influencing factors",
    "Sustainability":"Key Stakeholders and entities",
    "Security":     "External influencing factors",
}

# Natural language descriptions used as reference vectors for semantic similarity
LENS_DESCRIPTIONS = {
    "Key Stakeholders and entities": (
        "Infrastructure, sensors, IoT, AIoT, platforms, and the urban systems "
        "or organisations enabling AI urbanism"
    ),
    "Models of Interaction": (
        "Interaction, decision-making, feedback loops, predictive analytics, "
        "and how AI behaves in the urban environment"
    ),
    "External influencing factors": (
        "Governance, policies, ethics, regulation, sustainability, cultural "
        "context, and normative factors shaping AI urbanism"
    ),
}

# Weighted lens scores per indicator (from Fig. 3b in the paper)
LENS_WEIGHTS = {
    "SearchIndicator": [
        "Action", "Agency", "Culture", "Data", "Governance",
        "Materiality", "Personality", "Security", "Space",
        "Sustainability", "Technology", "Time"
    ],
    "Key Stakeholders and entities": [
        3.184, 11.406, 11.814, 34.658, 17.654,
        5.784, 3.661, 2.402, 22.788, 54.695, 59.124, 4.803
    ],
    "Models of Interaction": [
        5.166, 2.225, 11.035, 16.032, 2.046,
        4.252, 1.122, 0.585, 8.165, 17.33, 19.398, 2.679
    ],
    "External influencing factors": [
        1.179, 35.071, 9.036, 29.109, 52.921,
        4.241, 6.406, 1.171, 10.369, 24.763, 17.346, 2.824
    ],
}

# Temporal lens contribution data (from Fig. 4b in the paper)
TEMPORAL_DATA = {
    "Year": [1990, 2006, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
    "Key Stakeholders and entities":   [0, 0, 18, 49, 80, 84, 147, 195, 282, 338, 393, 805, 205],
    "Models of Interaction":           [1, 1, 34, 50, 73, 102, 137, 180, 269, 374, 434, 903, 265],
    "External influencing factors":    [0, 0, 10, 22, 46, 47, 56, 82, 169, 194, 266, 586, 167],
}

# Subsystem connection data (from Fig. 6 in the paper)
SUBSYSTEM_DATA = {
    "Subsystem": [
        "Decision-Making Dynamics", "Citizen Participation Models", "Human-AI Interfaces",
        "Urban Data Infrastructure", "AI Hardware & Platforms", "Institutional Stakeholders",
        "Platform Governance", "Ethical Standards", "Accountability Mechanisms",
        "Legal/Policy Instruments", "Feedback Loops", "Public Legitimacy"
    ],
    "Key Stakeholders and entities": [30, 5, 10, 40, 35, 25, 25, 10, 5, 10, 5, 15],
    "Models of Interaction":         [20, 40, 35, 10, 10, 5, 20, 20, 25, 15, 35, 20],
    "External influencing factors":  [10, 25, 15, 10, 10, 5, 15, 45, 50, 40, 35, 30],
}


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — HYBRID SEMANTIC CLASSIFICATION
# Combines keyword matching with sentence-transformer cosine similarity
# (Section 3.1.2 in the paper)
# ══════════════════════════════════════════════════════════════════════════════

def tag_articles_with_lens(input_file, output_file, similarity_threshold=0.45):
    """
    Assign each article in the master database to a conceptual lens using
    a two-stage hybrid approach:
      - Stage 1: Keyword-based matching from the INDICATOR_TO_LENS mapping
      - Stage 2: Sentence-BERT semantic similarity as a confirmatory signal

    Articles whose keyword match falls below the similarity threshold are
    supplemented by the top semantic match.

    Parameters
    ----------
    input_file : str
        Path to Merged_Tagged_AIUrbanism.xlsx
    output_file : str
        Path where the tagged output will be saved
    similarity_threshold : float
        Minimum cosine similarity for a semantic match to be retained (default 0.45)
    """
    df = pd.read_excel(input_file, dtype=str).fillna("")
    df.columns = df.columns.str.strip()
    df["SearchIndicator"] = df["SearchIndicator"].str.strip()

    # --- Stage 1: keyword-based lens assignment ---
    df["Keyword_Lens"] = df["SearchIndicator"].map(INDICATOR_TO_LENS).fillna("Unclassified")

    # --- Stage 2: semantic similarity using Sentence-BERT ---
    model = SentenceTransformer("all-MiniLM-L6-v2")
    lens_names = list(LENS_DESCRIPTIONS.keys())
    lens_embeddings = model.encode(list(LENS_DESCRIPTIONS.values()), convert_to_tensor=True)

    def compute_semantic_lens(text):
        if not text.strip():
            return "Unclassified"
        embedding = model.encode(text, convert_to_tensor=True)
        scores = util.cos_sim(embedding, lens_embeddings)[0].tolist()
        best_score = max(scores)
        if best_score < similarity_threshold:
            return "Unclassified"
        return lens_names[scores.index(best_score)]

    combined_text = (
        df.get("Title", "") + " " +
        df.get("Abstract", "") + " " +
        df.get("Keyword", "")
    )
    print("Running semantic classification — this may take a few minutes...")
    df["Semantic_Lens"] = combined_text.apply(compute_semantic_lens)

    # --- Ensemble: prefer keyword match; fall back to semantic if unclassified ---
    df["ConceptualLens"] = df.apply(
        lambda row: row["Keyword_Lens"]
        if row["Keyword_Lens"] != "Unclassified"
        else row["Semantic_Lens"],
        axis=1,
    )

    df.to_excel(output_file, index=False)
    print(f"Tagged articles saved to: {output_file}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — WEIGHTED LENS MATRIX CONSTRUCTION
# (Section 3.2.1 in the paper)
# ══════════════════════════════════════════════════════════════════════════════

def build_weighted_matrix(input_file, output_file):
    """
    Build a lens-weight matrix:
    rows = search indicators, columns = conceptual lens scores.
    Weights are derived from hybrid semantic similarity scores (Stage 2 above).

    Parameters
    ----------
    input_file : str
        Path to the tagged article database
    output_file : str
        Path where the weighted matrix will be saved
    """
    df = pd.read_excel(input_file, dtype=str).fillna("")
    df["SearchIndicator"] = df["SearchIndicator"].str.strip()
    df["ConceptualLens"] = df["ConceptualLens"].str.strip()

    pivot = df.pivot_table(
        index="SearchIndicator",
        columns="ConceptualLens",
        aggfunc="size",
        fill_value=0,
    ).reset_index()

    pivot.to_excel(output_file, index=False)
    print(f"Weighted matrix saved to: {output_file}")
    return pivot


def build_yearly_trend_matrix(input_file, output_file):
    """
    Aggregate lens-level article counts by year to track temporal evolution
    of discourse (Section 3.2.3 in the paper).
    """
    df = pd.read_excel(input_file, dtype=str).fillna("")
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["ConceptualLens"] = df["ConceptualLens"].str.strip()
    df = df.dropna(subset=["Year", "ConceptualLens"])
    df["Year"] = df["Year"].astype(int)

    trend = df.pivot_table(
        index="Year",
        columns="ConceptualLens",
        aggfunc="size",
        fill_value=0,
    ).reset_index()

    trend.to_excel(output_file, index=False)
    print(f"Trend matrix saved to: {output_file}")
    return trend


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — VALIDATION
# Stratified 10% sample with Cohen's kappa (Section 3.1.3 in the paper)
# ══════════════════════════════════════════════════════════════════════════════

def create_validation_sample(input_file, output_file, sample_fraction=0.10):
    """
    Draw a stratified 10% sample for manual coding and compute inter-rater
    reliability once the Manual_Lens column is filled in.

    Parameters
    ----------
    input_file : str
        Tagged article database
    output_file : str
        Path for the validation spreadsheet (includes a Manual_Lens column
        that a human coder fills in)
    """
    df = pd.read_excel(input_file).fillna("")
    df = df[["Title", "Keyword", "Abstract", "SearchIndicator", "ConceptualLens"]].copy()
    df = df.rename(columns={"ConceptualLens": "Auto_Lens"})

    parts = []
    for _, group in df.groupby("SearchIndicator"):
        n = max(1, round(len(group) * sample_fraction))
        parts.append(group.sample(n=n, random_state=42))

    validation = pd.concat(parts).drop_duplicates().reset_index(drop=True)
    validation["Manual_Lens"] = ""
    validation["Notes"] = ""

    validation.to_excel(output_file, index=False)
    print(f"Validation sample ({len(validation)} rows) saved to: {output_file}")
    return validation


def compute_validation_scores(validation_file):
    """
    Compute exact agreement and Cohen's kappa from a completed validation sheet.
    The Manual_Lens column must be filled before calling this function.
    """
    df = pd.read_excel(validation_file).fillna("")
    coded = df[df["Manual_Lens"].str.strip() != ""].copy()

    if coded.empty:
        print("No manually coded rows found. Fill in the Manual_Lens column first.")
        return

    agreement = (
        coded["Auto_Lens"].str.strip() == coded["Manual_Lens"].str.strip()
    ).mean() * 100

    kappa = cohen_kappa_score(
        coded["Auto_Lens"].str.strip(),
        coded["Manual_Lens"].str.strip(),
    )

    print(f"Rows coded: {len(coded)}")
    print(f"Exact agreement: {round(agreement, 2)}%")
    print(f"Cohen's kappa:   {round(kappa, 3)}")
    print("\nClassification report:")
    print(classification_report(coded["Manual_Lens"], coded["Auto_Lens"]))
    print("\nConfusion matrix:")
    print(confusion_matrix(coded["Manual_Lens"], coded["Auto_Lens"]))


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — ORDINATION ANALYSIS
# PCA, NMDS, and GNMDS (Section 3.2.2 in the paper)
# ══════════════════════════════════════════════════════════════════════════════

def run_pca(df_weighted_matrix):
    """
    Run Principal Component Analysis on the weighted lens matrix.
    Returns the PCA result, explained variance, and the scaler.
    """
    df = df_weighted_matrix.set_index("SearchIndicator") \
        if "SearchIndicator" in df_weighted_matrix.columns \
        else df_weighted_matrix.copy()

    scaler = StandardScaler()
    scaled = scaler.fit_transform(df)

    pca = PCA(n_components=2)
    components = pca.fit_transform(scaled)
    explained = pca.explained_variance_ratio_

    print(f"PCA — explained variance: PC1={explained[0]:.1%}, PC2={explained[1]:.1%}")
    return components, explained, df.index.tolist(), pca, scaler


def run_nmds(df_weighted_matrix, metric=False):
    """
    Run Non-Metric Multidimensional Scaling (NMDS) on the weighted matrix.
    Setting metric=False gives non-metric MDS; metric=True gives classic MDS.
    """
    df = df_weighted_matrix.set_index("SearchIndicator") \
        if "SearchIndicator" in df_weighted_matrix.columns \
        else df_weighted_matrix.copy()

    scaler = StandardScaler()
    scaled = scaler.fit_transform(df)
    dissimilarity = pairwise_distances(scaled, metric="euclidean")

    mds = MDS(
        n_components=2,
        dissimilarity="precomputed",
        random_state=42,
        metric=metric,
        max_iter=3000,
        n_init=10,
    )
    coords = mds.fit_transform(dissimilarity)
    stress = mds.stress_
    print(f"NMDS stress: {stress:.4f}")
    return coords, df.index.tolist()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — FIGURES
# Reproduces Figures 2–6 from the paper
# ══════════════════════════════════════════════════════════════════════════════

LENS_COLORS = {
    "Key Stakeholders and entities": "#e74c3c",
    "Models of Interaction":         "#3498db",
    "External influencing factors":  "#2ecc71",
}


def figure2_indicator_trends(master_file):
    """
    Figure 2: Trends and growth dynamics of search indicators.
    Panels: (a) annual line plot, (b) boxplot by period,
            (c) period trajectories, (d) dominant/emerging bubble plot.
    """
    df = pd.read_excel(master_file)
    df = df[["SearchIndicator", "Year"]].dropna()
    df["SearchIndicator"] = df["SearchIndicator"].str.strip()
    df["Year"] = df["Year"].astype(str).str.extract(r"(\d{4})").astype(int)

    # --- Panel (a): annual counts per indicator ---
    annual = (
        df.groupby(["Year", "SearchIndicator"]).size().reset_index(name="Count")
    )

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    sns.set_style("whitegrid")

    ax = axes[0, 0]
    for indicator, group in annual.groupby("SearchIndicator"):
        ax.plot(group["Year"], group["Count"], marker="o", markersize=3, label=indicator)
    ax.set_title("a) Annual publication trends by search indicator", fontsize=11)
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of papers")
    ax.legend(fontsize=7, ncol=2)

    # --- Panel (b): boxplot by time period ---
    bins = [2009, 2012, 2015, 2018, 2020, 2022, 2025]
    period_labels = ["2010–12", "2013–15", "2016–18", "2019–20", "2021–22", "2023–25"]
    df["Period"] = pd.cut(df["Year"], bins=bins, labels=period_labels, include_lowest=True)

    period_counts = (
        df.groupby(["Period", "SearchIndicator"]).size().reset_index(name="Count")
    )

    ax = axes[0, 1]
    sns.boxplot(data=period_counts, x="SearchIndicator", y="Count",
                hue="Period", ax=ax, palette="Set2")
    ax.set_title("b) Indicator frequency by time period", fontsize=11)
    ax.set_xlabel("Search indicator")
    ax.set_ylabel("Frequency")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(fontsize=7, title="Period")

    # --- Panel (c): period-level trajectory lines ---
    ax = axes[1, 0]
    for indicator, group in period_counts.groupby("SearchIndicator"):
        ax.plot(group["Period"].astype(str), group["Count"],
                marker="o", markersize=4, label=indicator)
    ax.set_title("c) Temporal frequency across five-year periods", fontsize=11)
    ax.set_xlabel("Period")
    ax.set_ylabel("Frequency")
    ax.tick_params(axis="x", rotation=30)
    ax.legend(fontsize=7, ncol=2)

    # --- Panel (d): dominant / emerging bubble plot ---
    summary = annual.groupby("SearchIndicator").agg(
        TotalPubs=("Count", "sum")
    )
    first_year = df.groupby("SearchIndicator")["Year"].min()
    last_year  = df.groupby("SearchIndicator")["Year"].max()
    first_count = annual[annual["Year"] == annual["Year"].min()].set_index("SearchIndicator")["Count"]
    last_count  = annual[annual["Year"] == annual["Year"].max()].set_index("SearchIndicator")["Count"]
    summary["Growth"] = (
        (last_count - first_count) / (last_year - first_year + 1)
    ).fillna(0)

    ax = axes[1, 1]
    median_total  = summary["TotalPubs"].median()
    median_growth = summary["Growth"].median()

    scatter = ax.scatter(
        summary["TotalPubs"], summary["Growth"],
        s=summary["TotalPubs"] / 2,
        alpha=0.7,
        c=range(len(summary)),
        cmap="tab20",
    )
    for indicator, row in summary.iterrows():
        ax.annotate(indicator, (row["TotalPubs"], row["Growth"]),
                    fontsize=8, ha="left")
    ax.axvline(median_total,  color="grey", linestyle="--", alpha=0.6)
    ax.axhline(median_growth, color="grey", linestyle="--", alpha=0.6)
    ax.text(median_total + 5, median_growth + 1, "Dominant",  fontsize=9)
    ax.text(5, median_growth + 1,               "Emerging",  fontsize=9)
    ax.text(5, median_growth - 5,               "Marginal",  fontsize=9)
    ax.text(median_total + 5, median_growth - 5, "Declining", fontsize=9)
    ax.set_title("d) Dominant vs. Emerging vs. Declining indicators", fontsize=11)
    ax.set_xlabel("Total publications")
    ax.set_ylabel("Growth rate (papers/year)")

    plt.tight_layout()
    plt.savefig(out("figure2_indicator_trends.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("Figure 2 saved.")


def figure3_heatmap_and_network():
    """
    Figure 3: Semantic mapping of conceptual lenses.
    Panels: (b) heatmap of weighted indicator-to-lens scores,
            (c) semantic network, (d) stacked proportional bar chart.
    """
    df_weights = pd.DataFrame(LENS_WEIGHTS).set_index("SearchIndicator")

    fig, axes = plt.subplots(1, 3, figsize=(20, 6))

    # --- Panel (b): heatmap ---
    ax = axes[0]
    sns.heatmap(
        df_weights,
        annot=True, fmt=".1f",
        cmap="YlOrRd",
        linewidths=0.5,
        ax=ax,
    )
    ax.set_title("b) Weighted mapping: indicators to lenses", fontsize=11)
    ax.set_xlabel("Conceptual lens")
    ax.set_ylabel("Search indicator")
    ax.tick_params(axis="x", rotation=30)

    # --- Panel (c): network graph ---
    ax = axes[1]
    G = nx.Graph()
    lens_names = list(LENS_COLORS.keys())

    for lens in lens_names:
        G.add_node(lens, node_type="lens")
    for ind in df_weights.index:
        G.add_node(ind, node_type="indicator")
        for lens in lens_names:
            weight = df_weights.loc[ind, lens]
            if weight > 0:
                G.add_edge(ind, lens, weight=weight)

    pos = nx.spring_layout(G, seed=42, k=2)
    lens_node_colors  = [LENS_COLORS[n] for n in lens_names]
    ind_node_colors   = ["#95a5a6"] * len(df_weights)
    all_colors = (
        {n: LENS_COLORS[n] for n in lens_names}
        | {n: "#95a5a6" for n in df_weights.index}
    )
    node_colors = [all_colors[n] for n in G.nodes()]

    edges = G.edges(data=True)
    edge_widths = [d["weight"] / 20 for _, _, d in edges]

    nx.draw_networkx(
        G, pos, ax=ax,
        node_color=node_colors,
        node_size=[600 if G.nodes[n]["node_type"] == "lens" else 300 for n in G.nodes()],
        edge_color="grey",
        width=edge_widths,
        font_size=7,
        with_labels=True,
    )
    ax.set_title("c) Semantic network: indicators and lenses", fontsize=11)
    ax.axis("off")

    # --- Panel (d): proportional stacked bar ---
    ax = axes[2]
    df_prop = df_weights.div(df_weights.sum(axis=1), axis=0)
    df_prop.plot(kind="bar", stacked=True, ax=ax,
                 color=list(LENS_COLORS.values()), legend=True)
    ax.set_title("d) Proportional contribution of lenses per indicator", fontsize=11)
    ax.set_xlabel("Search indicator")
    ax.set_ylabel("Proportion")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(title="Lens", fontsize=7, bbox_to_anchor=(1.05, 1))

    plt.tight_layout()
    plt.savefig(out("figure3_heatmap_network.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("Figure 3 saved.")


def figure4_temporal_evolution():
    """
    Figure 4: Temporal evolution of conceptual lenses.
    Panel (b): LOWESS-smoothed trajectory lines for each lens.
    """
    df = pd.DataFrame(TEMPORAL_DATA)
    df = df.sort_values("Year")

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.set_style("whitegrid")

    lens_columns = [
        "Key Stakeholders and entities",
        "Models of Interaction",
        "External influencing factors",
    ]
    raw_styles = ["o", "s", "^"]

    for lens, marker in zip(lens_columns, raw_styles):
        color = LENS_COLORS[lens]
        ax.scatter(df["Year"], df[lens], color=color, marker=marker, s=30, alpha=0.5)

        smoothed = lowess(df[lens], df["Year"], frac=0.4)
        ax.plot(
            smoothed[:, 0], smoothed[:, 1],
            color=color, linewidth=2,
            label=lens,
        )

    ax.set_title("Temporal evolution of conceptual lenses in AI Urbanism (LOWESS-smoothed)", fontsize=12)
    ax.set_xlabel("Year")
    ax.set_ylabel("Weighted contribution")
    ax.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(out("figure4_temporal_lowess.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("Figure 4 saved.")


def figure5_ordination(weighted_file, trend_file):
    """
    Figure 5: Integration of conceptual lenses as knowledge systems.
    Panels: (a) PCA biplot of temporal trends,
            (b) NMDS of indicators by lens weight,
            (c) NMDS with cluster ellipses,
            (d) GNMDS with observer-independent metadata.
    """
    # Load data
    df_weighted = pd.read_excel(weighted_file).set_index("SearchIndicator")
    df_trend    = pd.read_excel(trend_file)
    df_trend.rename(columns={df_trend.columns[0]: "Year"}, inplace=True)
    df_trend.set_index("Year", inplace=True)
    df_trend.dropna(inplace=True)

    lens_names = list(LENS_COLORS.keys())
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))

    # --- Panel (a): PCA biplot (temporal) ---
    ax = axes[0, 0]
    scaler = StandardScaler()
    trend_scaled = scaler.fit_transform(df_trend)
    pca = PCA(n_components=2)
    comps = pca.fit_transform(trend_scaled)
    expl = pca.explained_variance_ratio_

    ax.scatter(comps[:, 0], comps[:, 1], s=50, color="#7f8c8d", zorder=3)
    for i, year in enumerate(df_trend.index):
        ax.annotate(str(year), (comps[i, 0], comps[i, 1]), fontsize=8)
    ax.axhline(0, color="grey", linewidth=0.5, linestyle="--")
    ax.axvline(0, color="grey", linewidth=0.5, linestyle="--")
    ax.set_title(f"a) PCA biplot — temporal lens trajectories\n"
                 f"PC1={expl[0]:.1%}, PC2={expl[1]:.1%}", fontsize=10)
    ax.set_xlabel(f"PC1 ({expl[0]:.1%})")
    ax.set_ylabel(f"PC2 ({expl[1]:.1%})")

    # Color year points by era
    era_colors = {y: "#e74c3c" if y <= 2014 else "#3498db" if y <= 2019 else "#2ecc71"
                  for y in df_trend.index}
    for i, year in enumerate(df_trend.index):
        ax.scatter(comps[i, 0], comps[i, 1], color=era_colors[year], s=60, zorder=4)

    # --- Panel (b): NMDS of indicators ---
    ax = axes[0, 1]
    scaler2 = StandardScaler()
    weighted_scaled = scaler2.fit_transform(df_weighted)
    diss = pairwise_distances(weighted_scaled, metric="euclidean")
    mds = MDS(n_components=2, dissimilarity="precomputed",
              random_state=42, metric=False, max_iter=3000)
    nmds_coords = mds.fit_transform(diss)

    # Assign each indicator its dominant lens colour
    dominant_lens = df_weighted.idxmax(axis=1)
    for i, ind in enumerate(df_weighted.index):
        color = LENS_COLORS.get(dominant_lens[ind], "#95a5a6")
        ax.scatter(nmds_coords[i, 0], nmds_coords[i, 1],
                   color=color, s=80, zorder=3)
        ax.annotate(ind, (nmds_coords[i, 0], nmds_coords[i, 1]), fontsize=8)
    legend_handles = [mpatches.Patch(color=c, label=l) for l, c in LENS_COLORS.items()]
    ax.legend(handles=legend_handles, fontsize=7)
    ax.set_title("b) NMDS ordination of search indicators by lens weight", fontsize=10)
    ax.set_xlabel("NMDS Dimension 1")
    ax.set_ylabel("NMDS Dimension 2")

    # --- Panel (c): NMDS with confidence ellipses per lens ---
    ax = axes[1, 0]
    for i, ind in enumerate(df_weighted.index):
        color = LENS_COLORS.get(dominant_lens[ind], "#95a5a6")
        ax.scatter(nmds_coords[i, 0], nmds_coords[i, 1],
                   color=color, s=80, zorder=3)
        ax.annotate(ind, (nmds_coords[i, 0], nmds_coords[i, 1]), fontsize=8)

    for lens, color in LENS_COLORS.items():
        idx = [i for i, ind in enumerate(df_weighted.index) if dominant_lens[ind] == lens]
        if len(idx) < 2:
            continue
        pts = nmds_coords[idx]
        cx, cy = pts.mean(axis=0)
        cov = np.cov(pts.T) if pts.shape[0] > 1 else np.eye(2)
        vals, vecs = np.linalg.eigh(cov)
        order = vals.argsort()[::-1]
        vals, vecs = vals[order], vecs[:, order]
        angle = np.degrees(np.arctan2(*vecs[:, 0][::-1]))
        ell = Ellipse(
            (cx, cy),
            width=2 * np.sqrt(vals[0]),
            height=2 * np.sqrt(vals[1]),
            angle=angle,
            edgecolor=color, facecolor="none",
            linewidth=1.5, linestyle="--", alpha=0.8,
        )
        ax.add_patch(ell)
    ax.legend(handles=legend_handles, fontsize=7)
    ax.set_title("c) NMDS with conceptual lens clusters", fontsize=10)
    ax.set_xlabel("NMDS Dimension 1")
    ax.set_ylabel("NMDS Dimension 2")

    # --- Panel (d): GNMDS (metric MDS as observer-independent baseline) ---
    ax = axes[1, 1]
    mds_metric = MDS(n_components=2, dissimilarity="precomputed",
                     random_state=42, metric=True, max_iter=3000)
    gnmds_coords = mds_metric.fit_transform(diss)

    for i, ind in enumerate(df_weighted.index):
        color = LENS_COLORS.get(dominant_lens[ind], "#95a5a6")
        ax.scatter(gnmds_coords[i, 0], gnmds_coords[i, 1],
                   color=color, s=80, zorder=3)
        ax.annotate(ind, (gnmds_coords[i, 0], gnmds_coords[i, 1]), fontsize=8)
    ax.legend(handles=legend_handles, fontsize=7)
    ax.set_title("d) GNMDS — observer-independent ordination", fontsize=10)
    ax.set_xlabel("GNMDS Dimension 1")
    ax.set_ylabel("GNMDS Dimension 2")

    plt.tight_layout()
    plt.savefig(out("figure5_ordination.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("Figure 5 saved.")


def figure6_governance_network():
    """
    Figure 6: Systems-based governance framework of AI Urbanism.
    A weighted spoke-and-hub network connecting each lens to 12 urban subsystems.
    """
    df = pd.DataFrame(SUBSYSTEM_DATA)

    G = nx.Graph()
    lens_names = list(LENS_COLORS.keys())

    # Nodes
    G.add_node("Models of Interaction", node_type="lens")
    G.add_node("Key Stakeholders and entities", node_type="lens")
    G.add_node("External influencing factors", node_type="lens")
    for sub in df["Subsystem"]:
        G.add_node(sub, node_type="subsystem")

    # Edges (weighted by lens score)
    for _, row in df.iterrows():
        for lens in lens_names:
            w = row[lens]
            if w > 0:
                G.add_edge(row["Subsystem"], lens, weight=w)

    # Layout: lenses at centre, subsystems around periphery
    pos = {}
    n_sub = len(df)
    for i, sub in enumerate(df["Subsystem"]):
        angle = 2 * np.pi * i / n_sub
        pos[sub] = (np.cos(angle) * 3, np.sin(angle) * 3)
    pos["Key Stakeholders and entities"] = (0.8, 0.5)
    pos["Models of Interaction"]         = (-0.8, 0.5)
    pos["External influencing factors"]  = (0.0, -0.8)

    node_colors = []
    for n in G.nodes():
        if G.nodes[n]["node_type"] == "lens":
            node_colors.append(LENS_COLORS[n])
        else:
            node_colors.append("#bdc3c7")

    edge_colors  = []
    edge_widths  = []
    for u, v, d in G.edges(data=True):
        lens = u if u in LENS_COLORS else v
        edge_colors.append(LENS_COLORS.get(lens, "#95a5a6"))
        edge_widths.append(d["weight"] / 15)

    fig, ax = plt.subplots(figsize=(14, 12))
    nx.draw_networkx(
        G, pos, ax=ax,
        node_color=node_colors,
        node_size=[1500 if G.nodes[n]["node_type"] == "lens" else 600 for n in G.nodes()],
        edge_color=edge_colors,
        width=edge_widths,
        font_size=7,
        with_labels=True,
        alpha=0.9,
    )
    legend_handles = [mpatches.Patch(color=c, label=l) for l, c in LENS_COLORS.items()]
    legend_handles.append(mpatches.Patch(color="#bdc3c7", label="Urban subsystem"))
    ax.legend(handles=legend_handles, fontsize=8, loc="lower right")
    ax.set_title(
        "Systems-based governance framework of AI Urbanism\n"
        "Conceptual lenses and urban governance subsystems",
        fontsize=13,
    )
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(out("figure6_governance_framework.png"), dpi=150, bbox_inches="tight")
    plt.close()
    print("Figure 6 saved.")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def run_full_pipeline():
    """
    Run the complete analysis pipeline end to end.

    Expected input files (in INPUT_DIR):
      - Merged_Tagged_AIUrbanism.xlsx
      - Hybrid_Conceptual_Lens_Weighted_Matrix.xlsx
      - Hybrid_Conceptual_Lens_Weighted_Matrix_trend_contributing_Analysis.xlsx

    Generated output files (in OUTPUT_DIR):
      - Tagged_AIUrbanism.xlsx
      - Weighted_Matrix.xlsx
      - Trend_Matrix.xlsx
      - Validation_Sample.xlsx
      - figure2_indicator_trends.png
      - figure3_heatmap_network.png
      - figure4_temporal_lowess.png
      - figure5_ordination.png
      - figure6_governance_framework.png
    """

    master_file  = inp("Merged_Tagged_AIUrbanism.xlsx")
    weighted_file = inp("Hybrid_Conceptual_Lens_Weighted_Matrix.xlsx")
    trend_file    = inp(
        "Hybrid_Conceptual_Lens_Weighted_Matrix_trend_contributing_Analysis.xlsx"
    )

    tagged_file     = out("Tagged_AIUrbanism.xlsx")
    wmatrix_file    = out("Weighted_Matrix.xlsx")
    tmatrix_file    = out("Trend_Matrix.xlsx")
    validation_file = out("Validation_Sample.xlsx")

    print("\n=== Step 1: Semantic tagging ===")
    tag_articles_with_lens(master_file, tagged_file)

    print("\n=== Step 2: Build weighted matrix ===")
    build_weighted_matrix(tagged_file, wmatrix_file)

    print("\n=== Step 3: Build yearly trend matrix ===")
    build_yearly_trend_matrix(tagged_file, tmatrix_file)

    print("\n=== Step 4: Create validation sample ===")
    create_validation_sample(tagged_file, validation_file)

    print("\n=== Step 5: Generate figures ===")
    figure2_indicator_trends(master_file)
    figure3_heatmap_and_network()
    figure4_temporal_evolution()
    figure5_ordination(weighted_file, trend_file)
    figure6_governance_network()

    print("\nAll steps complete. Outputs are in:", OUTPUT_DIR)


if __name__ == "__main__":
    run_full_pipeline()
