from db import run_query

def route_avoiding_line(start, end, forbidden_line):
    query = """
    MATCH (s:Station {name:$start}), (t:Station {name:$end})
    MATCH p = shortestPath((s)-[*]-(t))
    WHERE NONE(r IN relationships(p) WHERE type(r) = $line)
    RETURN
      [n IN nodes(p) | n.name] AS stations,
      [r IN relationships(p) | type(r)] AS lines,
      length(p) AS hops
    """

    df = run_query(query, {
        "start": start,
        "end": end,
        "line": forbidden_line
    })

    if df.empty:
        return {
            "stations": [start, end],
            "hops": 1,
            "note": "No route avoiding this line"
        }

    return df.iloc[0].to_dict()
    
