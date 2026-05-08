# download.py
import urllib.request
import os
from pathlib import Path

Path('data/raw').mkdir(parents=True, exist_ok=True)

# PatentsView latest release URLs
# Adjust the date slug if yours is different (check data.patentsview.org)
BASE = "https://s3.amazonaws.com/data.patentsview.org/20231231/download"

FILES = {
    "g_patent.tsv.zip":                f"{BASE}/g_patent.tsv.zip",
    "g_patent_abstract.tsv.zip":       f"{BASE}/g_patent_abstract.tsv.zip",
    "g_persistent_inventor.tsv.zip":   f"{BASE}/g_persistent_inventor.tsv.zip",
    "g_persistent_assignee.tsv.zip":   f"{BASE}/g_persistent_assignee.tsv.zip",
    "g_location_disambiguated.tsv.zip":f"{BASE}/g_location_disambiguated.tsv.zip",
}

def download(url, dest):
    print(f"Downloading {dest}...")
    def progress(count, block, total):
        if total > 0:
            pct = count * block * 100 // total
            print(f"  {pct}%", end='\r')
    urllib.request.urlretrieve(url, dest, reporthook=progress)
    size = os.path.getsize(dest)
    print(f"  ✓ {dest} — {size/1e6:.1f} MB")

for fname, url in FILES.items():
    dest = f"data/raw/{fname}"
    # Skip if already downloaded and >1MB (not a failed download)
    if os.path.exists(dest) and os.path.getsize(dest) > 1_000_000:
        print(f"  ✓ {fname} already exists ({os.path.getsize(dest)/1e6:.1f} MB) — skipping")
        continue
    try:
        download(url, dest)
    except Exception as e:
        print(f"  ✗ Failed: {e}")

print("\nDone. Run: ls -lh data/raw/")