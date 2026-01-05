from db import run_query

def list_stations(limit=1000):
    query = """
    MATCH (s:Station)
    RETURN s.name AS station, s.zone AS zone
    ORDER BY s.name
    LIMIT $limit
    """
    df = run_query(query, {"limit": limit})
    if df.empty:
      return []
    return df.to_dict(orient="records")

def list_lines():
    query = """
    CALL db.relationshipTypes()
    """
    df = run_query(query)
    return df["relationshipType"].tolist()

def network_stats():
    query = """
    MATCH (s:Station)
    WITH count(s) AS stations
    MATCH ()-[r]-()
    RETURN stations, count(r)/2 AS connections
    """
    df = run_query(query)
    return df.iloc[0].to_dict()
