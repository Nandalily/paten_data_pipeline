# cat > app.py << 'EOF'
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
# if not os.path.exists("patents.db"):
#     import etl  # or subprocess.run(["python", "etl.py"])

st.set_page_config(
    page_title="Global Patent Intelligence",
    page_icon="🔬",
    layout="wide"
)

# @st.cache_resource
# def get_conn():
#     return sqlite3.connect('patents.db', check_same_thread=False)

# @st.cache_data
# def query(sql):
#     return pd.read_sql(sql, get_conn())
@st.cache_data
def load_data():
    patents    = pd.read_csv("data/clean/clean_patents.csv")
    locations  = pd.read_csv("data/clean/clean_locations.csv")
    gov        = pd.read_csv("data/clean/clean_gov_interest.csv")
    contracts  = pd.read_csv("data/clean/clean_contracts.csv")
    return patents, locations, gov, contracts

patents_df, locations_df, gov_df, contracts_df = load_data()

# Lightweight in-memory SQL via DuckDB
import duckdb

@st.cache_data
def query(sql):
    return duckdb.query(sql).df()

# ── Header ────────────────────────────────────────────────
st.title("Global Patent Intelligence")
st.caption("Chunked ETL from USPTO PatentsView · SQL analytics · Built for exploration and demos.")

# ── Metric cards ──────────────────────────────────────────
total_patents  = query("SELECT COUNT(*) as n FROM patents").iloc[0,0]
total_locs     = query("SELECT COUNT(*) as n FROM locations").iloc[0,0]
total_gov      = query("SELECT COUNT(*) as n FROM gov_interest").iloc[0,0]
total_contracts= query("SELECT COUNT(*) as n FROM contracts").iloc[0,0]
total_countries= query("SELECT COUNT(DISTINCT country) as n FROM locations WHERE country IS NOT NULL").iloc[0,0]
with_claims    = query("SELECT COUNT(*) as n FROM patents WHERE num_claims IS NOT NULL").iloc[0,0]

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Patents",      f"{total_patents:,}")
c2.metric("Locations",    f"{total_locs:,}")
c3.metric("Countries",    f"{total_countries:,}")
c4.metric("Gov Interest", f"{total_gov:,}")
c5.metric("Contracts",    f"{total_contracts:,}")
c6.metric("With Claims",  f"{with_claims:,}")

st.divider()

# ── Tabs ──────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs([
    "📊 Overview",
    "🔍 Patent search",
    "🌍 Countries",
    "📈 Trends",
    "🏛 Gov interest",
    "🏆 Top patents",
    "💻 SQL demos (Q1–Q7)"
])

# ── Tab 1: Overview ───────────────────────────────────────
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("What you are looking at")
        st.markdown("""
        - **Patents** are utility patents from USPTO PatentsView (2018 sample)
        - **Locations** come from the disambiguated location table with country/city/state
        - **Gov interest** records patents with US government funding or rights
        - **Contracts** link patents to specific government contract award numbers
        - Tabs to the right drill into countries, trends, rankings and SQL demos (Q1–Q7)
        """)
        st.subheader("Data files loaded")
        files = {
            "g_patent.tsv.zip": f"{total_patents:,} patents",
            "g_location_disambiguated.tsv.zip": f"{total_locs:,} locations",
            "g_gov_interest.tsv.zip": f"{total_gov:,} records",
            "g_gov_interest_contracts.tsv.zip": f"{total_contracts:,} contracts",
            "g_patent_abstract.tsv.zip": "⏳ uploading",
            "g_persistent_inventor.tsv.zip": "⏳ pending",
            "g_persistent_assignee.tsv.zip": "⏳ pending",
        }
        for fname, status in files.items():
            st.markdown(f"- `{fname}` — {status}")

    with col2:
        st.subheader("Quick trend preview")
        trends = query("""
            SELECT year, COUNT(*) as patents
            FROM patents GROUP BY year ORDER BY year
        """)
        fig = px.line(trends, x='year', y='patents',
                      markers=True,
                      labels={'patents':'Patents granted','year':'Year'})
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=300)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Patent types")
        types = query("""
            SELECT patent_type, COUNT(*) as count
            FROM patents GROUP BY patent_type ORDER BY count DESC
        """)
        fig2 = px.bar(types, x='patent_type', y='count',
                      labels={'patent_type':'Type','count':'Count'})
        fig2.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=250)
        st.plotly_chart(fig2, use_container_width=True)

# ── Tab 2: Patent search ──────────────────────────────────
with tab2:
    st.subheader("Search patents")
    col1, col2 = st.columns([3,1])
    with col1:
        keyword = st.text_input("Search in title", placeholder="e.g. machine learning, battery, sensor")
    with col2:
        limit = st.selectbox("Results", [10, 25, 50, 100], index=0)

    if keyword:
        results = query(f"""
            SELECT patent_id, title, filing_date, year, num_claims
            FROM patents
            WHERE LOWER(title) LIKE LOWER('%{keyword}%')
            ORDER BY num_claims DESC
            LIMIT {limit}
        """)
        st.write(f"Found **{len(results)}** results for *{keyword}*")
        st.dataframe(results, use_container_width=True)
    else:
        st.info("Enter a keyword above to search patent titles")
        st.subheader("Sample patents")
        sample = query("SELECT patent_id, title, filing_date, num_claims FROM patents LIMIT 20")
        st.dataframe(sample, use_container_width=True)

# ── Tab 3: Countries ──────────────────────────────────────
with tab3:
    st.subheader("Q3 — Locations by country")
    countries = query("""
        SELECT country, COUNT(*) as locations
        FROM locations
        WHERE country IS NOT NULL AND country != ''
        GROUP BY country ORDER BY locations DESC
    """)

    col1, col2 = st.columns(2)
    with col1:
        top_n = st.slider("Show top N countries", 5, 50, 15)
        df = countries.head(top_n)
        fig = px.bar(df, x='country', y='locations',
                     labels={'country':'Country','locations':'Inventor locations'},
                     color='locations', color_continuous_scale='Blues')
        fig.update_layout(margin=dict(l=0,r=0,t=10,b=0), height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.pie(countries.head(10), values='locations', names='country',
                      title='Top 10 countries share')
        fig2.update_layout(margin=dict(l=0,r=0,t=40,b=0), height=400)
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(countries, use_container_width=True)
    countries.to_csv('reports/top_countries.csv', index=False)

# ── Tab 4: Trends ─────────────────────────────────────────
with tab4:
    st.subheader("Q4 — Patent trends over time")
    st.info("Currently showing 2018 sample. Trends will expand once more year files are loaded.")

    trends = query("""
        SELECT year, COUNT(*) as patents,
               AVG(num_claims) as avg_claims
        FROM patents GROUP BY year ORDER BY year
    """)

    fig = px.bar(trends, x='year', y='patents',
                 labels={'patents':'Patents granted','year':'Year'},
                 title='Patents granted per year')
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Claims distribution")
    claims = query("SELECT num_claims FROM patents WHERE num_claims IS NOT NULL AND num_claims < 100")
    fig2 = px.histogram(claims, x='num_claims', nbins=50,
                        labels={'num_claims':'Number of claims'},
                        title='Distribution of patent claims')
    fig2.update_layout(height=300)
    st.plotly_chart(fig2, use_container_width=True)

# ── Tab 5: Gov interest ───────────────────────────────────
with tab5:
    st.subheader("Government interest patents")

    gov_count = query("""
        SELECT COUNT(DISTINCT p.patent_id) as gov_patents,
               COUNT(DISTINCT p.patent_id) * 100.0 / (SELECT COUNT(*) FROM patents) as pct
        FROM patents p JOIN gov_interest g ON p.patent_id = g.patent_id
    """)
    col1, col2, col3 = st.columns(3)
    col1.metric("Gov-linked patents", f"{gov_count.iloc[0,0]:,}")
    col2.metric("% of total", f"{gov_count.iloc[0,1] or 0:.1f}%")
    col3.metric("Unique contracts", f"{total_contracts:,}")

    st.subheader("Sample — patents with government interest")
    gov_patents = query("""
        SELECT p.patent_id, p.title, p.year, p.num_claims,
               SUBSTR(g.gi_statement, 1, 120) as gi_summary
        FROM patents p
        JOIN gov_interest g ON p.patent_id = g.patent_id
        LIMIT 50
    """)
    st.dataframe(gov_patents, use_container_width=True)

# ── Tab 6: Top patents ────────────────────────────────────
with tab6:
    st.subheader("Q7 — Top patents ranked by claims")
    ranked = query("""
        SELECT patent_id,
               title,
               num_claims,
               year,
               RANK() OVER (ORDER BY num_claims DESC) as rank
        FROM patents
        WHERE num_claims IS NOT NULL
        LIMIT 50
    """)
    fig = px.bar(ranked.head(20), x='num_claims', y='patent_id',
                 orientation='h',
                 hover_data=['title'],
                 labels={'num_claims':'Number of claims','patent_id':'Patent ID'},
                 title='Top 20 patents by claim count')
    fig.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(ranked, use_container_width=True)

# ── Tab 7: SQL demos ──────────────────────────────────────
with tab7:
    st.subheader("SQL query demos — Q1 through Q7")

    queries_map = {
        "Q1 — Most active years": """
            SELECT year, COUNT(*) as patents
            FROM patents GROUP BY year
            ORDER BY patents DESC LIMIT 10""",

        "Q2 — Top gov interest statements": """
            SELECT SUBSTR(gi_statement,1,80) as statement, COUNT(*) as count
            FROM gov_interest
            GROUP BY gi_statement
            ORDER BY count DESC LIMIT 10""",

        "Q3 — Top countries": """
            SELECT country, COUNT(*) as locations
            FROM locations
            WHERE country IS NOT NULL
            GROUP BY country ORDER BY locations DESC LIMIT 15""",

        "Q4 — Patent trends by year": """
            SELECT year, COUNT(*) as patents
            FROM patents GROUP BY year ORDER BY year""",

        "Q5 — JOIN patents + gov interest": """
            SELECT p.patent_id, SUBSTR(p.title,1,60) as title,
                   p.year, SUBSTR(g.gi_statement,1,80) as gi_summary
            FROM patents p
            JOIN gov_interest g ON p.patent_id = g.patent_id
            LIMIT 10""",

        "Q6 — CTE with running total": """
            WITH yearly AS (
                SELECT year, COUNT(*) as patents
                FROM patents GROUP BY year
            )
            SELECT year, patents,
                   SUM(patents) OVER (ORDER BY year) as running_total
            FROM yearly ORDER BY year""",

        "Q7 — Ranking by num_claims": """
            SELECT patent_id, SUBSTR(title,1,50) as title,
                   num_claims, year,
                   RANK() OVER (ORDER BY num_claims DESC) as rank
            FROM patents
            WHERE num_claims IS NOT NULL LIMIT 15""",
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

# EOF

