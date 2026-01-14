from routes_basic import fastest_route
from routes_transfers import least_transfer_route
from routes_congestion import find_congestion_aware_route
from routes_avoid_line import route_avoiding_line
from routes_info import network_stats
from db import close_driver

def print_route(title, route):
    print(f"\n=== {title} ===")
    for k, v in route.items():
        print(f"{k}: {v}")

def main():
    try:
        # Show stats
        stats = network_stats()
        print(f"Network Stats: {stats['stations']} stations, {stats['connections']} connections")

        start = "Paddington"
        end = "Stratford"

        print("\nLondon Underground Route Optimizer")
        print(f"From {start} to {end}")

        # Feature 1
        print("\n[DEBUG] Running fastest_route...")
        r1 = fastest_route(start, end)
        print_route("Fastest route", r1)

        # Feature 2
        try:
            print("\n[DEBUG] Running least_transfer_route...")
            r2 = least_transfer_route(start, end)
            print_route("Least-transfer route", r2)
        except Exception as e:
            print("\nLeast-transfer route failed (acceptable):", e)

        # Feature 3
        print("\n[DEBUG] Running congestion-aware route...")
        r3 = find_congestion_aware_route(start, end)
        print_route("Congestion-aware route", r3)

        # Feature 4
        avoid_line = "ELIZABETH"
        print(f"\n[DEBUG] Running route avoiding {avoid_line} line...")
        r4 = route_avoiding_line(start, end, avoid_line)
        print_route(f"Route avoiding {avoid_line}", r4)

    finally:
        close_driver()

if __name__ == "__main__":
    main()
