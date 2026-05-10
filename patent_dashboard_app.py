import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os

st.set_page_config(
    page_title="Global Patent Intelligence",
    page_icon="🔬",
    layout="wide"
)

# ── Build DB from CSVs on cold start ─────────────────────
DB_PATH = "patents.db"

@st.cache_resource
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")

    # Create and load tables if empty
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS contracts (
            patent_id TEXT, contract_award_number TEXT
        );
        CREATE TABLE IF NOT EXISTS gov_interest (
            patent_id TEXT, gi_statement TEXT
        );
        CREATE TABLE IF NOT EXISTS locations (
            location_id TEXT, country TEXT, city TEXT, state TEXT
        );
    """)

    # Load CSVs only if tables are empty
    cur = conn.cursor()
    for table, path in [
        ("contracts",    "data/clean/clean_contracts.csv"),
        ("gov_interest", "data/clean/clean_gov_interest.csv"),
        ("locations",    "data/clean/clean_locations.csv"),
    ]:
        count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if count == 0 and os.path.exists(path):
            df = pd.read_csv(path)
            df.to_sql(table, conn, if_exists="replace", index=False)
    conn.commit()
    return conn

@st.cache_data
def query(sql):
    return pd.read_sql(sql, get_conn())

# ── Header ────────────────────────────────────────────────
st.title("🔬 Global Patent Intelligence")
st.caption("USPTO PatentsView · SQL analytics · Built for exploration and demos.")

# ── Metric cards ──────────────────────────────────────────
total_contracts  = query("SELECT COUNT(*) as n FROM contracts").iloc[0,0]
total_gov        = query("SELECT COUNT(*) as n FROM gov_interest").iloc[0,0]
total_locs       = query("SELECT COUNT(*) as n FROM locations").iloc[0,0]
total_countries  = query("SELECT COUNT(DISTINCT country) as n FROM locations WHERE country IS NOT NULL").iloc[0,0]
unique_patents   = query("SELECT COUNT(DISTINCT patent_id) as n FROM gov_interest").iloc[0,0]
unique_contracts = query("SELECT COUNT(DISTINCT contract_award_number) as n FROM contracts").iloc[0,0]

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Gov Interest Records", f"{total_gov:,}")
c2.metric("Unique Patents",        f"{unique_patents:,}")
c3.metric("Contracts",             f"{total_contracts:,}")
c4.metric("Unique Contract IDs",   f"{unique_contracts:,}")
c5.metric("Locations",             f"{total_locs:,}")
c6.metric("Countries",             f"{total_countries:,}")

st.divider()

# ── Tabs ──────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "🌍 Countries",
    "🏛 Gov Interest",
    "📋 Contracts",
    "💻 SQL Demos"
])

# ── Tab 1: Overview ───────────────────────────────────────
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("About this dataset")
        st.markdown("""
        - **Gov Interest** — patents with US government funding or rights
        - **Contracts** — patent links to government contract award numbers
        - **Locations** — disambiguated inventor locations with country/city/state
        """)
        st.subheader("Files loaded")
        st.markdown(f"""
        - `clean_gov_interest.csv` — {total_gov:,} records
        - `clean_contracts.csv` — {total_contracts:,} records
        - `clean_locations.csv` — {total_locs:,} locations
        """)

    with col2:
        st.subheader("Top 10 countries by inventor locations")
        top_countries = query("""
            SELECT country, COUNT(*) as locations
            FROM locations
            WHERE country IS NOT NULL AND country != ''
            GROUP BY country ORDER BY locations DESC LIMIT 10
        """)
        fig = px.bar(top_countries, x='country', y='locations',
                     color='locations', color_continuous_scale='Blues',
                     labels={'country':'Country','locations':'Locations'})
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=350)
        st.plotly_chart(fig, use_container_width=True)

# ── Tab 2: Countries ──────────────────────────────────────
with tab2:
    st.subheader("Inventor locations by country")
    countries = query("""
        SELECT country, COUNT(*) as locations
        FROM locations
        WHERE country IS NOT NULL AND country != ''
        GROUP BY country ORDER BY locations DESC
    """)

    col1, col2 = st.columns(2)
    with col1:
        top_n = st.slider("Show top N countries", 5, 50, 15)
        fig = px.bar(countries.head(top_n), x='country', y='locations',
                     color='locations', color_continuous_scale='Blues',
                     labels={'country':'Country','locations':'Inventor locations'})
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.pie(countries.head(10), values='locations', names='country',
                      title='Top 10 countries share')
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(countries, use_container_width=True)

# ── Tab 3: Gov Interest ───────────────────────────────────
with tab3:
    st.subheader("Patents with government interest")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total gov interest records", f"{total_gov:,}")
    with col2:
        st.metric("Unique patents with gov interest", f"{unique_patents:,}")

    st.subheader("Search gov interest statements")
    keyword = st.text_input("Filter by keyword", placeholder="e.g. energy, defense, health")
    if keyword:
        results = query(f"""
            SELECT patent_id,
                   SUBSTR(gi_statement, 1, 200) as gi_summary
            FROM gov_interest
            WHERE LOWER(gi_statement) LIKE LOWER('%{keyword}%')
            LIMIT 100
        """)
        st.write(f"**{len(results)}** results for *{keyword}*")
        st.dataframe(results, use_container_width=True)
    else:
        sample = query("""
            SELECT patent_id, SUBSTR(gi_statement, 1, 150) as gi_summary
            FROM gov_interest LIMIT 50
        """)
        st.dataframe(sample, use_container_width=True)

    st.subheader("Most common gov interest statements")
    common = query("""
        SELECT SUBSTR(gi_statement, 1, 80) as statement, COUNT(*) as count
        FROM gov_interest
        GROUP BY gi_statement
        ORDER BY count DESC LIMIT 15
    """)
    fig = px.bar(common, x='count', y='statement', orientation='h',
                 labels={'count':'Count','statement':'Statement'},
                 title='Top 15 most repeated gov interest statements')
    fig.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

# ── Tab 4: Contracts ──────────────────────────────────────
with tab4:
    st.subheader("Government contracts linked to patents")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total contract records", f"{total_contracts:,}")
    with col2:
        st.metric("Unique contract award numbers", f"{unique_contracts:,}")

    st.subheader("Patents per contract")
    per_contract = query("""
        SELECT contract_award_number, COUNT(*) as patents
        FROM contracts
        GROUP BY contract_award_number
        ORDER BY patents DESC LIMIT 20
    """)
    fig = px.bar(per_contract, x='patents', y='contract_award_number',
                 orientation='h',
                 labels={'patents':'Patents linked','contract_award_number':'Contract ID'},
                 title='Top 20 contracts by number of linked patents')
    fig.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Full contracts table")
    st.dataframe(
        query("SELECT * FROM contracts LIMIT 200"),
        use_container_width=True
    )

# ── Tab 5: SQL Demos ──────────────────────────────────────
with tab5:
    st.subheader("SQL query demos")

    queries_map = {
        "Q1 — Top countries by locations": """
            SELECT country, COUNT(*) as locations
            FROM locations
            WHERE country IS NOT NULL
            GROUP BY country ORDER BY locations DESC LIMIT 15""",

        "Q2 — Most common gov interest statements": """
            SELECT SUBSTR(gi_statement,1,80) as statement, COUNT(*) as count
            FROM gov_interest
            GROUP BY gi_statement
            ORDER BY count DESC LIMIT 10""",

        "Q3 — Patents with contracts": """
            SELECT patent_id, COUNT(*) as num_contracts
            FROM contracts
            GROUP BY patent_id
            ORDER BY num_contracts DESC LIMIT 15""",

        "Q4 — JOIN gov interest + contracts": """
            SELECT g.patent_id,
                   SUBSTR(g.gi_statement,1,80) as gi_summary,
                   c.contract_award_number
            FROM gov_interest g
            JOIN contracts c ON g.patent_id = c.patent_id
            LIMIT 20""",

        "Q5 — Cities with most locations": """
            SELECT city, country, COUNT(*) as count
            FROM locations
            WHERE city IS NOT NULL AND city != ''
            GROUP BY city, country
            ORDER BY count DESC LIMIT 15""",

        "Q6 — CTE: patents in both tables": """
            WITH gov AS (SELECT DISTINCT patent_id FROM gov_interest),
                 con AS (SELECT DISTINCT patent_id FROM contracts)
            SELECT COUNT(*) as in_both
            FROM gov JOIN con ON gov.patent_id = con.patent_id""",

        "Q7 — US states with most locations": """
            SELECT state, COUNT(*) as locations
            FROM locations
            WHERE country = 'US' AND state IS NOT NULL
            GROUP BY state ORDER BY locations DESC LIMIT 15""",
    }

    selected = st.selectbox("Choose a query", list(queries_map.keys()))
    sql = queries_map[selected]
    st.code(sql.strip(), language='sql')
    result = query(sql)
    st.dataframe(result, use_container_width=True)
    st.download_button(
        "⬇ Download as CSV",
        result.to_csv(index=False),
        file_name=f"{selected[:20].replace(' ','_')}.csv"
    )
