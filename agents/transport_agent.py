from utils.llm import generate_structured
from utils.schemas import (
    BudgetAllocation,
    TransportAgentOutput,
    TripRequest,
)


SYSTEM_INSTRUCTION = (
    "You are a Transportation Specialist Agent in a multi-agent travel planning system. "
    "Compare realistic intercity travel options (flights, trains, buses, or road) between the "
    "starting location and destination for all travellers combined (round-trip or full journey). "
    "Respect the allocated transportation budget ceiling whenever realistic, provide honest "
    "duration and total cost estimates in INR, and set data_source to 'ai_estimated'."
)


def _get_category_budget(allocation: BudgetAllocation, category_name: str) -> float:
    for item in allocation.categories:
        if item.category.lower() == category_name.lower():
            return item.allocated_amount
    return 0.0


def run_transport_agent(
    request: TripRequest,
    resolved_destination: str,
    allocation: BudgetAllocation,
    feedback: str = "",
) -> TransportAgentOutput:
    """
    Generates 2-3 realistic transportation options within the allocated transport budget.
    Supports optional feedback from the Review Agent for replanning.
    """
    transport_budget = _get_category_budget(allocation, "Transportation")
    feedback_clause = f"\nReviewer Replanning Feedback to Address: {feedback}\n" if feedback else ""

    prompt = (
        f"Starting Location: {request.starting_location}\n"
        f"Destination: {resolved_destination}\n"
        f"Number of Travellers: {request.travellers}\n"
        f"Trip Duration: {request.days} days\n"
        f"Preferred Transport Mode: {request.transport_preference}\n"
        f"Allocated Transportation Budget (Total for {request.travellers} travellers): ₹{transport_budget:,.2f}\n"
        f"{feedback_clause}\n"
        "Provide 2 to 3 realistic transport options (e.g., Train, Flight, Bus/Car) with "
        "estimated_total_cost covering all travellers for the trip. "
        "Set recommended_option_index to the best budget-and-comfort fit, and set data_source to 'ai_estimated'."
    )

    result = generate_structured(
        prompt=prompt,
        response_schema=TransportAgentOutput,
        system_instruction=SYSTEM_INSTRUCTION,
    )
    result.data_source = "ai_estimated"
    for opt in result.options:
        opt.data_source = "ai_estimated"
    return result