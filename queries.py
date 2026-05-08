# cat > queries.py << 'EOF'
import sqlite3
import pandas as pd
import json
import pathlib

pathlib.Path('reports').mkdir(exist_ok=True)
conn = sqlite3.connect('patents.db')

print("=" * 55)
print("     GLOBAL PATENT INTELLIGENCE REPORT")
print("=" * 55)

total = conn.execute("SELECT COUNT(*) FROM patents").fetchone()[0]
yr = conn.execute("SELECT MIN(year),MAX(year) FROM patents").fetchone()
print(f"\nTotal Patents:  {total:,}")
print(f"Year range:     {yr[0]} – {yr[1]}")

# Q1 — Most active years (proxy for top inventors until file arrives)
print("\n── Q1: Most active years ──────────────────────────")
q1 = pd.read_sql("""
    SELECT year, COUNT(*) as patents
    FROM patents GROUP BY year
    ORDER BY patents DESC LIMIT 10
""", conn)
print(q1.to_string(index=False))

# Q2 — Top government agencies
print("\n── Q2: Top government interest patents ────────────")
q2 = pd.read_sql("""
    SELECT gi_statement, COUNT(*) as count
    FROM gov_interest
    GROUP BY gi_statement
    ORDER BY count DESC LIMIT 10
""", conn)
print(q2.to_string(index=False))

# Q3 — Top countries
print("\n── Q3: Top countries ──────────────────────────────")
q3 = pd.read_sql("""
    SELECT country, COUNT(*) as locations
    FROM locations
    WHERE country IS NOT NULL AND country != ''
    GROUP BY country
    ORDER BY locations DESC LIMIT 15
""", conn)
print(q3.to_string(index=False))
q3.to_csv('reports/top_countries.csv', index=False)

# Q4 — Trends over time
print("\n── Q4: Patent trends by year ──────────────────────")
q4 = pd.read_sql("""
    SELECT year, COUNT(*) as patents
    FROM patents
    GROUP BY year ORDER BY year
""", conn)
print(q4.to_string(index=False))
q4.to_csv('reports/country_trends.csv', index=False)

# Q5 — JOIN patents with gov interest
print("\n── Q5: JOIN — patents with gov interest ───────────")
q5 = pd.read_sql("""
    SELECT p.patent_id, p.title, p.year, g.gi_statement
    FROM patents p
    JOIN gov_interest g ON p.patent_id = g.patent_id
    LIMIT 10
""", conn)
print(q5.to_string(index=False))

# Q6 — CTE with running total
print("\n── Q6: CTE — yearly counts + running total ────────")
q6 = pd.read_sql("""
    WITH yearly AS (
        SELECT year, COUNT(*) as patents
        FROM patents GROUP BY year
    )
    SELECT year, patents,
           SUM(patents) OVER (ORDER BY year) as running_total
    FROM yearly ORDER BY year
""", conn)
print(q6.to_string(index=False))

# Q7 — Ranking by num_claims
print("\n── Q7: Ranking — top patents by claims ────────────")
q7 = pd.read_sql("""
    SELECT patent_id,
           SUBSTR(title,1,50) as title,
           num_claims, year,
           RANK() OVER (ORDER BY num_claims DESC) as rank
    FROM patents
    WHERE num_claims IS NOT NULL
    LIMIT 15
""", conn)
print(q7.to_string(index=False))
q7.to_csv('reports/top_patents_by_claims.csv', index=False)

# JSON report
report = {
    "total_patents": total,
    "year_range": {"from": int(yr[0]), "to": int(yr[1])},
    "top_countries": q3.head(10).to_dict('records'),
    "patent_trends": q4.to_dict('records'),
    "top_by_claims": q7.head(10).to_dict('records'),
    "top_gov_agencies": q2.head(10).to_dict('records')
}
with open('reports/report.json', 'w') as f:
    json.dump(report, f, indent=2)

print("\n✅ Reports saved to reports/")
print("   - reports/top_countries.csv")
print("   - reports/country_trends.csv")
print("   - reports/top_patents_by_claims.csv")
print("   - reports/report.json")
print("\nRun next: streamlit run app.py")
conn.close()
# EOF

# python queries.py