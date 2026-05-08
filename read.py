import pandas as pd

def load_sample(filepath, nrows=50000):
    chunks = []
    for chunk in pd.read_csv(filepath, sep='\t', chunksize=10000,
                              nrows=nrows, low_memory=False, 
                              on_bad_lines='skip'):
        chunks.append(chunk)
    return pd.concat(chunks, ignore_index=True)

patents_raw = load_sample('data/raw/g_patent.tsv.zip', nrows=50000)