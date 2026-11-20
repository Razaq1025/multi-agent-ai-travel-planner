from services.budget_engine import allocate_budget, validate_estimated_expenses
from services.external_apis import fetch_place_coordinates, fetch_weather_data
from services.route_optimizer import optimize_itinerary_routes
from utils.schemas import ActivityItem, DayItinerary, TripRequest


def test_deterministic_budget_exact_sum():
    req = TripRequest(
        starting_location="Visakhapatnam",
        destination="Goa",
        days=4,
        travellers=3,
        total_budget=33333.33,
        interests=["Beaches"],
        accommodation_preference="Mid-range",
    )
    allocation = allocate_budget(req)
    total_allocated = round(sum(c.allocated_amount for c in allocation.categories), 2)
    assert total_allocated == 33333.33
    assert allocation.data_source == "deterministic_calculation"
    assert allocation.is_feasible is True


def test_tight_budget_warning():
    req = TripRequest(
        starting_location="Visakhapatnam",
        destination="Goa",
        days=5,
        travellers=2,
        total_budget=5000.0,
        interests=["Beaches"],
    )
    allocation = allocate_budget(req)
    assert allocation.is_feasible is False
    assert len(allocation.warnings) >= 1


def test_expense_reconciliation():
    req = TripRequest(
        starting_location="Visakhapatnam",
        destination="Goa",
        days=3,
        travellers=2,
        total_budget=20000.0,
        interests=["Food"],
    )
    allocation = allocate_budget(req)
    summary = validate_estimated_expenses(
        allocation=allocation,
        transport_cost=5000.0,
        accommodation_cost=6000.0,
        food_cost=3000.0,
        activities_cost=2000.0,
    )
    assert summary["spendable_budget"] == 19000.0
    assert summary["total_estimated_cost"] == 16000.0
    assert summary["within_budget"] is True


def test_external_api_fallback_provenance():
    weather = fetch_weather_data("Goa", "November")
    assert weather["data_source"] in ("live_api", "mock_api")

    coords = fetch_place_coordinates("Goa", ["Baga Beach", "Fort Aguada", "Basilica of Bom Jesus"])
    assert coords["data_source"] in ("live_api", "mock_api")
    assert len(coords["places"]) == 3


def test_ortools_route_optimizer():
    day = DayItinerary(
        day=1,
        theme="North Goa Heritage & Coast",
        area_focus="North Goa",
        activities=[
            ActivityItem(
                time_slot="Morning",
                place_name="Baga Beach",
                area="Baga",
                description="Beach walk",
                estimated_duration_hours=2.0,
                estimated_cost_total=500.0,
            ),
            ActivityItem(
                time_slot="Afternoon",
                place_name="Fort Aguada",
                area="Candolim",
                description="Historic fort",
                estimated_duration_hours=2.0,
                estimated_cost_total=300.0,
            ),
            ActivityItem(
                time_slot="Evening",
                place_name="Chapora Fort",
                area="Vagator",
                description="Sunset viewpoint",
                estimated_duration_hours=2.0,
                estimated_cost_total=200.0,
            ),
        ],
        recommended_restaurants=["Brittos", "Thalassa"],
        estimated_day_cost=2500.0,
    )
    opt_days, metrics = optimize_itinerary_routes("Goa", [day])
    assert len(opt_days) == 1
    assert len(opt_days[0].activities) == 3
    assert metrics["optimized_transit_km"] <= metrics["original_transit_km"]