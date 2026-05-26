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


def get_year(year):
    print(f"Getting results for {year}")
    results = d.search(
        q="", 
        style="metal", 
        type="master", 
        format="album", 
        genre="rock", 
        year=str(year)
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
    all_data.extend(get_year(year))
# %%
import json

with open('data.json', 'w') as f:
    json.dump(all_data, f, indent=4, ensure_ascii=False)

# %%

# %%
get_year(1979)

#%%

print(results.count)
# %%
results.page(1)
# %%
dir(foo)
