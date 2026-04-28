-- Top Inventors
SELECT name, COUNT(*) patents
FROM inventors
GROUP BY name
ORDER BY patents DESC
LIMIT 10;

-- Top Companies
SELECT company_id, COUNT(*) patents
FROM companies
GROUP BY company_id
ORDER BY patents DESC
LIMIT 10;

-- Trends
SELECT year, COUNT(*) patents
FROM patents
GROUP BY year
ORDER BY year;
