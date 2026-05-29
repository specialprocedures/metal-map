# %%
import json
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfTransformer
from hdbscan import HDBSCAN
import matplotlib.pyplot as plt

from umap import UMAP
import regex as re
import numpy as np
import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity

with open("data.json", "r") as f:
    data = json.load(f)

# %%

parsed = []
for item in data:
    artist, album = [i.strip() for i in item["title"].split(" - ", maxsplit=1)]
    item["artist"] = artist
    item["album"] = album

    parsed.append(item)
# %%

KEEP = [
    "id",
    "master_id",
    "uri",
    "title",
    "album",
    "artist",
    "label",
    "country",
    "year",
    "genre",
    "style",
    "want",
    "have",
    "thumb",
    "cover_image",
]

df = (
    pd.json_normalize(parsed)
    .rename(columns={"community.want": "want", "community.have": "have"})[KEEP]
    .drop_duplicates("id")
)

df["popularity"] = df["want"] + df["have"]
artist_counts = df["artist"].value_counts()

# %%

mlb = MultiLabelBinarizer()

styles = pd.DataFrame(
    mlb.fit_transform(df["style"]), columns=mlb.classes_, index=df.index
)
style_labels = [i for i in mlb.classes_]

top_styles = styles.sum().sort_values(ascending=False).head(100).index


df = (
    (
        pd.concat([df, styles], axis=1)
        .groupby(["artist"])[["popularity"] + style_labels]
        .sum()
        .merge(artist_counts.rename("artist_count"), left_on="artist", right_index=True)
    )
    .loc[lambda x: x["artist_count"] > 1]
    .loc[lambda x: x["popularity"] > 2000]
    .loc[lambda x: x[top_styles].sum(axis=1) > 0]  # sum of styles > 0
).reset_index()

# Drop any Hard Rock with popularity less than 3000
df = df[~((df["Hard Rock"] > 0) & (df["popularity"] < 3000))]

df["pop_log"] = np.log1p(df["popularity"])
df["pop_norm"] = df["pop_log"] / df["pop_log"].max()


# Strip anything matching (N) where N is a number from the artist name
df["artist"] = df["artist"].apply(lambda x: re.sub(r"\(\d+\)", "", x).strip())

# Strip asterixes from the artist name
df["artist"] = df["artist"].apply(lambda x: x.replace("*", "").strip())

# Drop artists with characters outside Latin + common European diacritics (Latin-1, U+0000–U+00FF)
df = df[~df["artist"].str.contains(r"[^\x00-\xFF]", regex=True)]
# %%

umap_model = UMAP(
    n_components=2,
    n_neighbors=250,
    min_dist=0.22,
    metric="cosine",
    random_state=42,
    densmap=True,  # preserves relative local density
    repulsion_strength=1.0,  # push outliers back toward the pack
)


tfidf = TfidfTransformer()
tfidf_matrix = tfidf.fit_transform(df[style_labels])

df[["x", "y"]] = umap_model.fit_transform(tfidf_matrix.toarray())

# %%


clusterer = HDBSCAN(min_cluster_size=30, metric="euclidean")
df["cluster"] = clusterer.fit_predict(df[["x", "y"]])

# %%


# %%
plt.figure(figsize=(10, 10))
plt.scatter(
    df["x"], df["y"], s=df["pop_norm"] * 100, alpha=0.5, c=df["cluster"], cmap="tab10"
)
plt.show()


# %%

from adjustText import adjust_text

# Set noto sans font with cjk support
plt.rcParams["font.family"] = "Noto Sans CJK JP"

# Black background

fig, ax = plt.subplots(figsize=(75, 75))
ax.set_facecolor("black")
scatter = ax.scatter(
    df["x"],
    df["y"],
    marker="",
    # s=np.log(df["pop_norm"] + 1) * 20,
    # alpha=df["pop_norm"],
)

texts = []
for _, row in df.iterrows():
    fontsize = 8 + 12 * (np.exp(row["pop_norm"]) - 1) / (np.e - 1)
    texts.append(
        ax.text(row["x"], row["y"], row["artist"], fontsize=fontsize, color="white")
    )

# remove spines and ticks
ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
ax.set_xticks([])
ax.set_yticks([])

adjust_text(
    texts,
    force_text=1.85,
    force_explode=0.5,
    max_move=25,
    avoid_self=False,
    prevent_crossings=False,
    iter_lim=1000,
)

fig.savefig("umap_plot.svg", dpi=300, bbox_inches="tight")
# %%
