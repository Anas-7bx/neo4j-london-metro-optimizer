from db import run_query

def least_transfer_route(start, end):
    # 1. Find shortest path length first
    query_shortest = """
    MATCH (s:Station {name:$start}), (t:Station {name:$end})
    MATCH sp = shortestPath((s)-[*]-(t))
    RETURN length(sp) as minHops
    """
    df_short = run_query(query_shortest, {"start": start, "end": end})
    if df_short.empty:
        return {}
    
    min_hops = int(df_short.iloc[0]["minHops"])
    
    # 2. Search paths of length minHops and minHops+1
    # We use f-string injection for bounds which is safe here as min_hops is an integer from DB
    query_paths = f"""
    MATCH (s:Station {{name:$start}}), (t:Station {{name:$end}})
    MATCH p = (s)-[* {min_hops}..{min_hops+1} ]-(t)
    
    WITH p,
         [r IN relationships(p) | type(r)] AS lines,
         length(p) AS hops

    WITH
      [n IN nodes(p) | n.name] AS stations,
      hops,
      reduce(c=0, i IN range(1,size(lines)-1) |
        c + CASE WHEN lines[i] <> lines[i-1] THEN 1 ELSE 0 END
      ) AS lineChanges

    RETURN stations, hops, lineChanges
    ORDER BY lineChanges, hops
    LIMIT 1
    """

    df = run_query(query_paths, {"start": start, "end": end})
    if not df.empty:
        return df.iloc[0].to_dict()

    return {}