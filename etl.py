# etl.py
import pandas as pd
import sqlite3
import zipfile
from pathlib import Path

Path('data/clean').mkdir(exist_ok=True)
SAMPLE = None
DB = 'patents.db'

def read_zip(path, nrows=None):
    with zipfile.ZipFile(path) as z:
        tsv_name = [n for n in z.namelist() if n.endswith('.tsv')][0]
        with z.open(tsv_name) as f:
            return pd.read_csv(f, sep='\t', nrows=nrows,
                               low_memory=False, on_bad_lines='skip')

# ── 1. Patents ────────────────────────────────────────────
print("Loading patents...")
pat = read_zip('data/raw/g_patent.tsv.zip', nrows=SAMPLE)
pat = pat[pat['patent_type'] == 'utility'].copy()
pat['year'] = pd.to_datetime(pat['patent_date'], errors='coerce').dt.year
pat = pat.rename(columns={
    'patent_title': 'title',
    'patent_date':  'filing_date'
})
patents = pat[['patent_id','title','filing_date','year','num_claims']]\
            .dropna(subset=['patent_id','year'])\
            .drop_duplicates('patent_id')
patents['abstract'] = ''   # placeholder until abstract file is fixed
patents.to_csv('data/clean/clean_patents.csv', index=False)
print(f"  ✓ {len(patents):,} patents")

# ── 2. Locations ──────────────────────────────────────────
print("Loading locations...")
loc = read_zip('data/raw/g_location_disambiguated.tsv.zip')
loc = loc[['location_id','disambig_country','disambig_city','disambig_state']]\
         .rename(columns={
             'disambig_country': 'country',
             'disambig_city':    'city',
             'disambig_state':   'state'
         })
loc.to_csv('data/clean/clean_locations.csv', index=False)
print(f"  ✓ {len(loc):,} locations")

# ── 3. Gov interest ───────────────────────────────────────
print("Loading government interest...")
gov = read_zip('data/raw/g_gov_interest.tsv.zip')
print(f"  Gov columns: {list(gov.columns)}")
gov.to_csv('data/clean/clean_gov_interest.csv', index=False)
print(f"  ✓ {len(gov):,} gov interest records")

print("Loading government contracts...")
contracts = read_zip('data/raw/g_gov_interest_contracts.tsv.zip')
print(f"  Contract columns: {list(contracts.columns)}")
contracts.to_csv('data/clean/clean_contracts.csv', index=False)
print(f"  ✓ {len(contracts):,} contracts")

# ── 4. Placeholder tables (filled later) ─────────────────
inventors = pd.DataFrame(columns=['inventor_id','name','country'])
companies = pd.DataFrame(columns=['company_id','name'])
relationships = pd.DataFrame(columns=['patent_id','inventor_id','company_id'])

# ── 5. Load SQLite ────────────────────────────────────────
print("\nLoading into SQLite...")
conn = sqlite3.connect(DB)

patents.to_sql('patents',       conn, if_exists='replace', index=False)
loc.to_sql('locations',         conn, if_exists='replace', index=False)
gov.to_sql('gov_interest',      conn, if_exists='replace', index=False)
contracts.to_sql('contracts',   conn, if_exists='replace', index=False)
inventors.to_sql('inventors',   conn, if_exists='replace', index=False)
companies.to_sql('companies',   conn, if_exists='replace', index=False)
relationships.to_sql('relationships', conn, if_exists='replace', index=False)

conn.execute("CREATE INDEX IF NOT EXISTS idx_pat_year ON patents(year)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_pat_id   ON patents(patent_id)")
conn.commit()

print("\n── Database summary ──────────────────────────")
for t in ['patents','locations','gov_interest','contracts']:
    n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t:20s}  {n:>10,} rows")
conn.close()
print(f"\n✅ Done! Run next: python queries.py")