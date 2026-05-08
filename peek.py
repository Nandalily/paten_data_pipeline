# peek.py — final version
import pandas as pd
import zipfile
import pyzipper

files_to_peek = [
    'data/raw/g_patent.tsv.zip',
    'data/raw/g_patent_abstract.tsv.zip',
    'data/raw/g_persistent_inventor.tsv.zip',
    'data/raw/g_persistent_assignee.tsv.zip',
    'data/raw/g_location_disambiguated.tsv.zip',
]

def smart_read(fpath, nrows=5):
    # Try 1: standard zipfile
    try:
        with zipfile.ZipFile(fpath) as z:
            tsv_name = [n for n in z.namelist() if n.endswith('.tsv')][0]
            with z.open(tsv_name) as f:
                return pd.read_csv(f, sep='\t', nrows=nrows, low_memory=False)
    except Exception:
        pass

    # Try 2: deflate64 zip via pyzipper
    try:
        with pyzipper.AESZipFile(fpath) as z:
            tsv_name = [n for n in z.namelist() if n.endswith('.tsv')][0]
            with z.open(tsv_name) as f:
                return pd.read_csv(f, sep='\t', nrows=nrows, low_memory=False)
    except Exception:
        pass

    # Try 3: plain TSV misnamed as .zip
    try:
        return pd.read_csv(fpath, sep='\t', nrows=nrows,
                           low_memory=False, on_bad_lines='skip')
    except Exception as e:
        return f"FAILED: {e}"

for fpath in files_to_peek:
    result = smart_read(fpath)
    print(f"\n{'='*60}")
    print(f"FILE: {fpath.split('/')[-1]}")
    if isinstance(result, str):
        print(result)
    else:
        print(f"Columns: {list(result.columns)}")
        print(result.head(2).to_string())