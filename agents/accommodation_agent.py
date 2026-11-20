from utils.llm import generate_structured
from utils.schemas import (
    AccommodationAgentOutput,
    BudgetAllocation,
    TripRequest,
)


SYSTEM_INSTRUCTION = (
    "You are an Accommodation Specialist Agent in a multi-agent travel planning system. "
    "Recommend realistic hotel, resort, or homestay options matching the user's tier, "
    "group size, number of nights, and allocated accommodation budget. "
    "Never claim live room availability; set data_source to 'ai_estimated'."
)


def _get_category_budget(allocation: BudgetAllocation, category_name: str) -> float:
    for item in allocation.categories:
        if item.category.lower() == category_name.lower():
            return item.allocated_amount
    return 0.0


def run_accommodation_agent(
    request: TripRequest,
    resolved_destination: str,
    allocation: BudgetAllocation,
    feedback: str = "",
) -> AccommodationAgentOutput:
    """
    Generates 2-3 realistic stay recommendations matching nights and accommodation budget.
    """
    accom_budget = _get_category_budget(allocation, "Accommodation")
    nights = max(1, request.days - 1)
    per_night_target = round(accom_budget / nights, 2)
    feedback_clause = f"\nReviewer Replanning Feedback to Address: {feedback}\n" if feedback else ""

    prompt = (
        f"Destination: {resolved_destination}\n"
        f"Number of Nights: {nights} (for a {request.days}-day trip)\n"
        f"Number of Travellers: {request.travellers}\n"
        f"Preferred Tier: {request.accommodation_preference}\n"
        f"Allocated Accommodation Budget (Total for {nights} nights): ₹{accom_budget:,.2f} "
        f"(approx. ₹{per_night_target:,.2f}/night)\n"
        f"{feedback_clause}\n"
        "Provide 2 to 3 realistic stay options in convenient neighborhoods, with realistic "
        "estimated_cost_per_night and estimated_total_cost for the entire stay in INR. "
        "Set recommended_option_index to the best value option, and set data_source to 'ai_estimated'."
    )

    result = generate_structured(
        prompt=prompt,
        response_schema=AccommodationAgentOutput,
        system_instruction=SYSTEM_INSTRUCTION,
    )
    result.data_source = "ai_estimated"
    for opt in result.options:
        opt.data_source = "ai_estimated"
    return result