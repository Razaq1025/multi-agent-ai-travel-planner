from typing import Dict, List
from utils.schemas import BudgetAllocation, BudgetCategory, TripRequest


ALLOCATION_PROFILES: Dict[str, Dict[str, float]] = {
    "Budget": {
        "Transportation": 0.35,
        "Accommodation": 0.25,
        "Food": 0.22,
        "Activities": 0.13,
        "Emergency": 0.05,
    },
    "Mid-range": {
        "Transportation": 0.30,
        "Accommodation": 0.35,
        "Food": 0.20,
        "Activities": 0.10,
        "Emergency": 0.05,
    },
    "Luxury": {
        "Transportation": 0.25,
        "Accommodation": 0.45,
        "Food": 0.15,
        "Activities": 0.10,
        "Emergency": 0.05,
    },
}

CATEGORY_NOTES: Dict[str, str] = {
    "Transportation": "Intercity travel (flights/trains/buses) plus local cabs/rentals",
    "Accommodation": "Hotels, resorts, or homestays including taxes",
    "Food": "Daily meals, local cuisine, cafes, and bottled water",
    "Activities": "Entry tickets, guided tours, water sports, and local experiences",
    "Emergency": "Unforeseen delays, medical buffer, and last-minute surcharges",
}

MIN_DAILY_PER_PERSON_INR = 1200.0


def allocate_budget(request: TripRequest) -> BudgetAllocation:
    """
    Deterministically allocates total_budget across 5 categories based on accommodation tier,
    ensuring exact sum reconciliation and feasibility warnings.
    """
    tier = request.accommodation_preference if request.accommodation_preference in ALLOCATION_PROFILES else "Mid-range"
    weights = ALLOCATION_PROFILES[tier]

    total_budget = round(float(request.total_budget), 2)
    categories: List[BudgetCategory] = []
    running_sum = 0.0

    items = list(weights.items())
    for idx, (cat_name, weight) in enumerate(items):
        if idx < len(items) - 1:
            allocated = round(total_budget * weight, 2)
            running_sum = round(running_sum + allocated, 2)
        else:
            # Assign exact remainder to the final category so sum == total_budget strictly
            allocated = round(total_budget - running_sum, 2)

        per_person = round(allocated / request.travellers, 2)
        categories.append(
            BudgetCategory(
                category=cat_name,
                allocated_amount=allocated,
                percentage=round(weight * 100, 1),
                per_person_amount=per_person,
                notes=CATEGORY_NOTES[cat_name],
            )
        )

    daily_per_person = total_budget / (request.days * request.travellers)
    warnings: List[str] = []
    is_feasible = True

    if daily_per_person < MIN_DAILY_PER_PERSON_INR:
        is_feasible = False
        warnings.append(
            f"Tight budget alert: ₹{daily_per_person:,.2f}/person/day is below the recommended "
            f"minimum of ₹{MIN_DAILY_PER_PERSON_INR:,.0f}/person/day for intercity travel + stay."
        )

    if tier == "Luxury" and daily_per_person < 6000.0:
        warnings.append(
            "Luxury accommodation selected, but daily per-person budget is under ₹6,000; "
            "consider switching to Mid-range stays."
        )

    return BudgetAllocation(
        total_budget=total_budget,
        currency="INR",
        categories=categories,
        is_feasible=is_feasible,
        warnings=warnings,
        data_source="deterministic_calculation",
    )


def validate_estimated_expenses(
    allocation: BudgetAllocation,
    transport_cost: float,
    accommodation_cost: float,
    food_cost: float,
    activities_cost: float,
) -> Dict[str, object]:
    """
    Deterministically compares agent-estimated expenses against allocated budget.
    """
    spendable_budget = sum(
        c.allocated_amount for c in allocation.categories if c.category != "Emergency"
    )
    total_estimated = round(transport_cost + accommodation_cost + food_cost + activities_cost, 2)
    difference = round(spendable_budget - total_estimated, 2)

    return {
        "spendable_budget": round(spendable_budget, 2),
        "total_estimated_cost": total_estimated,
        "remaining_or_overrun": difference,
        "within_budget": total_estimated <= spendable_budget,
    }