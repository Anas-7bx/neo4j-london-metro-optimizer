"""Single source of truth for the Neo4j database connection.

Credentials are read from environment variables (see .env.example at the
project root). The driver is created once and shared across all route modules.
"""

import os

from neo4j import GraphDatabase
import pandas as pd


URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")
DATABASE = os.getenv("NEO4J_DATABASE", "london")

if not PASSWORD:
    raise RuntimeError(
        "NEO4J_PASSWORD environment variable is required. "
        "Copy .env.example to .env and fill in your Neo4j credentials, "
        "or export the variables in your shell."
    )

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD), database=DATABASE)


def run_query(query, params=None):
    with driver.session() as session:
        result = session.run(query, params)
        return pd.DataFrame([r.data() for r in result])


print(f"Connected to {DATABASE}")


def close_driver():
    driver.close()
