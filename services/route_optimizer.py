import math
from typing import Dict, List, Tuple
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from services.external_apis import fetch_place_coordinates
from utils.schemas import ActivityItem, DayItinerary


TIME_SLOT_ORDER = ["Morning", "Afternoon", "Evening"]


def _haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    """
    Computes great-circle distance between two (lat, lng) points in integer meters.
    """
    radius_m = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return int(round(radius_m * c))


def _compute_path_distance_m(order: List[int], dist_matrix: List[List[int]]) -> int:
    total = 0
    for i in range(len(order) - 1):
        total += dist_matrix[order[i]][order[i + 1]]
    return total


def _solve_open_tsp_ortools(dist_matrix: List[List[int]]) -> List[int]:
    """
    Uses Google OR-Tools RoutingModel to find the shortest open path starting at index 0
    and visiting all stops without requiring a return to the start node (dummy depot trick).
    """
    n = len(dist_matrix)
    if n <= 2:
        return list(range(n))

    # Add a dummy depot node (index n) with 0 distance to all nodes so OR-Tools solves an open path
    size = n + 1
    augmented = [[0] * size for _ in range(size)]
    for i in range(n):
        for j in range(n):
            augmented[i][j] = dist_matrix[i][j]

    manager = pywrapcp.RoutingIndexManager(size, 1, n)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index: int, to_index: int) -> int:
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return augmented[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_params)
    if not solution:
        return list(range(n))

    ordered_nodes: List[int] = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        if node < n:
            ordered_nodes.append(node)
        index = solution.Value(routing.NextVar(index))

    return ordered_nodes if len(ordered_nodes) == n else list(range(n))


def optimize_itinerary_routes(
    destination: str,
    days: List[DayItinerary],
) -> Tuple[List[DayItinerary], Dict[str, object]]:
    """
    Optimizes the visiting order of activities within each day using Google OR-Tools
    and returns the reordered DayItinerary list along with optimization metrics.
    """
    optimized_days: List[DayItinerary] = []
    total_original_m = 0
    total_optimized_m = 0
    coord_source = "mock_api"

    for day in days:
        acts = day.activities
        if len(acts) <= 1:
            optimized_days.append(day)
            continue

        place_names = [a.place_name for a in acts]
        coord_payload = fetch_place_coordinates(destination, place_names)
        coord_source = str(coord_payload["data_source"])
        coords = coord_payload["places"]

        n = len(acts)
        dist_matrix = [
            [
                0
                if i == j
                else _haversine_meters(
                    coords[i]["lat"], coords[i]["lng"], coords[j]["lat"], coords[j]["lng"]
                )
                for j in range(n)
            ]
            for i in range(n)
        ]

        orig_order = list(range(n))
        best_order = _solve_open_tsp_ortools(dist_matrix)

        orig_dist = _compute_path_distance_m(orig_order, dist_matrix)
        opt_dist = _compute_path_distance_m(best_order, dist_matrix)

        # Keep original order if OR-Tools didn't strictly improve distance
        if opt_dist >= orig_dist:
            best_order = orig_order
            opt_dist = orig_dist

        total_original_m += orig_dist
        total_optimized_m += opt_dist

        reordered_activities: List[ActivityItem] = []
        for new_idx, old_idx in enumerate(best_order):
            item = acts[old_idx].model_copy()
            if new_idx < len(TIME_SLOT_ORDER):
                item.time_slot = TIME_SLOT_ORDER[new_idx]
            reordered_activities.append(item)

        updated_day = day.model_copy(update={"activities": reordered_activities})
        optimized_days.append(updated_day)

    saved_km = round(max(0, total_original_m - total_optimized_m) / 1000.0, 2)
    metrics = {
        "solver": "Google OR-Tools (RoutingModel / PATH_CHEAPEST_ARC)",
        "coordinate_source": coord_source,
        "original_transit_km": round(total_original_m / 1000.0, 2),
        "optimized_transit_km": round(total_optimized_m / 1000.0, 2),
        "distance_saved_km": saved_km,
    }

    return optimized_days, metrics