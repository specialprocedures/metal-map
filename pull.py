# %%
import os
from dotenv import load_dotenv

from tqdm import tqdm
import discogs_client

load_dotenv()

API_KEY = os.environ["DISCOGS_API_KEY"]
d = discogs_client.Client("igdr.ch", user_token=API_KEY)
# %%

years = list(range(1968, 2001))
styles = [
    "hard rock",
    # "punk",
    "metal",
    "grunge",
    "thrash",
    "hardcore",
    "stoner rock",
    # "space rock",
    "industrial",
]


def get_year(year, style="metal"):
    print(f"Getting results for {year} and style {style}")
    results = d.search(
        q="", style=style, type="master", format="album", genre="rock", year=str(year)
    )
    results.per_page = 100
    num_results = results.count
    num_pages = results.pages

    out = []

    for page in tqdm(range(num_pages)):
        try:
            results_page = results.page(page)
        except:
            Warning(f"Something went wrong on page {page} of {year}")
            continue

        for n, item in enumerate(results_page):
            out.append(item.data)
    return out


all_data = []
for year in tqdm(years):
    for style in styles:
        all_data.extend(get_year(year, style=style))
# %%
import json

with open("data.json", "w") as f:
    json.dump(all_data, f, indent=4, ensure_ascii=False)

# %%
