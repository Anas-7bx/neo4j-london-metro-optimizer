from db import run_query

def fastest_route(start, end):
    query = """
    MATCH (s:Station {name:$start}), (t:Station {name:$end})
    MATCH p = shortestPath((s)-[*]-(t))
    RETURN
      [n IN nodes(p) | n.name] AS stations,
      [r IN relationships(p) | type(r)] AS lines,
      length(p) AS hops
    """
    df = run_query(query, {"start": start, "end": end})
    return df.iloc[0].to_dict()
