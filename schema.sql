CREATE TABLE patents (
patent_id TEXT PRIMARY KEY,
title TEXT,
filing_date TEXT,
year INTEGER
);

CREATE TABLE inventors (
inventor_id TEXT,
patent_id TEXT,
name TEXT,
location_id TEXT
);

CREATE TABLE companies (
patent_id TEXT,
company_id TEXT
);

CREATE TABLE relationships (
patent_id TEXT,
inventor_id TEXT,
company_id TEXT
);
