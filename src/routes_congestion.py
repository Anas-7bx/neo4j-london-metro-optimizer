from db import run_query

# -------------------------------
# Baseline route (shortest path)
# -------------------------------

def get_baseline_route(start_station, end_station):
    query = """
    MATCH (start:Station {name: $start}),
          (end:Station {name: $end})
    MATCH p = shortestPath((start)-[*]-(end))
    WITH 
      [n IN nodes(p) | n.name] AS stations,
      [r IN relationships(p) | type(r)] AS lines
    WITH stations, lines,
         reduce(
           changes = 0,
           i IN range(1, size(lines)-1) |
           changes + CASE WHEN lines[i] <> lines[i-1] THEN 1 ELSE 0 END
         ) AS lineChanges
    RETURN stations, lines, size(stations)-1 AS hops, lineChanges
    """
    df = run_query(query, {"start": start_station, "end": end_station})
    return df.iloc[0].to_dict()

# -------------------------------
# Congestion model
# -------------------------------

def get_congestion_map():
    query = """
    MATCH (s:Station)-[r]-()
    RETURN s.name AS station, count(DISTINCT type(r)) AS lineCount
    """
    df = run_query(query)
    return {
        row["station"]: row["lineCount"]
        for _, row in df.iterrows()
    }

# -------------------------------
# Cost function (heuristic)
# -------------------------------

def compute_route_cost(route_info, congestion_map):
    if not route_info:
        return float("inf")

    stations = route_info["stations"]
    hops = route_info["hops"]
    line_changes = route_info.get("lineChanges", 0)

    # Ignore start & end for congestion
    congestion_cost = sum(
        congestion_map.get(station, 0)
        for station in stations[1:-1]
    )

    cost = (
        hops
        + 2 * line_changes
        + 0.5 * congestion_cost
    )

    return cost

# -------------------------------
# Identify bad stations in route
# -------------------------------

def get_bad_stations_in_route(route, congestion_map, threshold=5):
    return [
        s for s in route["stations"][1:-1]
        if congestion_map.get(s, 0) >= threshold
    ]

# -------------------------------
# Local rerouting (bounded)
# -------------------------------

def reroute_avoiding_station(start, end, forbidden_station, max_hops=8):
    # First try all shortest paths avoiding the forbidden station (fast)
    query_shortest = """
    MATCH (start:Station {name: $start}), (end:Station {name: $end})
    MATCH p = allShortestPaths((start)-[*]-(end))
    WITH p, [n IN nodes(p) | n.name] AS stations
    WHERE NOT $forbidden IN stations
    RETURN stations, length(p) AS hops
    LIMIT 1
    """

    df = run_query(query_shortest, {
        "start": start,
        "end": end,
        "forbidden": forbidden_station
    })

    if not df.empty:
        result = df.iloc[0].to_dict()
        result["lineChanges"] = 0
        return result

    # Fallback: bounded search inserting max_hops literal
    query = f"""
    MATCH (s:Station {{name:$start}}), (t:Station {{name:$end}})
    MATCH p = (s)-[*..{max_hops}]-(t)
    WHERE NOT $forbidden IN [n IN nodes(p) | n.name]
    RETURN
      [n IN nodes(p) | n.name] AS stations,
      length(p) AS hops
    ORDER BY length(p)
    LIMIT 1
    """

    df = run_query(query, {
        "start": start,
        "end": end,
        "forbidden": forbidden_station
    })

    if df.empty:
        return None

    result = df.iloc[0].to_dict()
    result["lineChanges"] = 0
    return result

# -------------------------------
# Build full alternative route
# -------------------------------

def build_alternative_route(base_route, forbidden_station, congestion_map):
    stations = base_route["stations"]

    if forbidden_station not in stations:
        return None

    idx = stations.index(forbidden_station)
    if idx == 0 or idx == len(stations) - 1:
        return None

    start = stations[idx - 1]
    end = stations[idx + 1]

    subpath = reroute_avoiding_station(start, end, forbidden_station)
    if not subpath:
        return None

    new_stations = (
        stations[:idx - 1]
        + subpath["stations"]
        + stations[idx + 2:]
    )

    new_route = {
        "stations": new_stations,
        "hops": len(new_stations) - 1,
        "lineChanges": 0
    }

    new_route["cost"] = compute_route_cost(new_route, congestion_map)
    return new_route

# -------------------------------
# Main Logic Wrapper
# -------------------------------

import concurrent.futures

def find_congestion_aware_route(start, end):
    congestion = get_congestion_map()
    base = get_baseline_route(start, end)
    base["cost"] = compute_route_cost(base, congestion)

    best = base
    bad_stations = get_bad_stations_in_route(base, congestion)

    # Parallelize the search for alternative routes
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all reroute tasks
        future_to_station = {
            executor.submit(build_alternative_route, base, bad, congestion): bad
            for bad in bad_stations
        }
        
        for future in concurrent.futures.as_completed(future_to_station):
            alt = future.result()
            if alt and alt["cost"] < best["cost"]:
                best = alt
    
    return best
