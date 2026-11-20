from utils.llm import generate_structured
from utils.schemas import DestinationAgentOutput, TripRequest


SYSTEM_INSTRUCTION = (
    "You are a Destination Specialist Agent in a multi-agent travel planning system. "
    "Recommend practical, budget-aligned destinations based on the user's starting location, "
    "interests, travel duration, and per-person daily budget. "
    "All cost estimates must be realistic in INR and clearly marked as ai_estimated."
)


def run_destination_agent(request: TripRequest) -> DestinationAgentOutput:
    """
    Evaluates the user's requested destination (or suggests one if none was provided)
    and generates 2 budget-compatible alternative destinations.
    """
    daily_per_person = round(request.total_budget / (request.days * request.travellers), 2)
    target_dest = (request.destination or "").strip()

    if target_dest:
        dest_clause = (
            f"The user has requested '{target_dest}' as their primary destination. "
            f"Use '{target_dest}' as primary_destination, explain why it fits their interests, "
            f"and provide 2 strong alternative destinations with a similar budget and vibe."
        )
    else:
        dest_clause = (
            "The user did not specify a destination. Recommend the best-fitting primary_destination "
            "reachable from their starting location within their budget, plus 2 strong alternatives."
        )

    prompt = (
        f"Starting Location: {request.starting_location}\n"
        f"Duration: {request.days} days\n"
        f"Travellers: {request.travellers}\n"
        f"Total Budget: ₹{request.total_budget:,.2f} (approx. ₹{daily_per_person:,.2f}/person/day)\n"
        f"Interests: {', '.join(request.interests)}\n"
        f"Accommodation Tier: {request.accommodation_preference}\n"
        f"Travel Month: {request.travel_month or 'Flexible'}\n"
        f"Additional Notes: {request.additional_notes or 'None'}\n\n"
        f"{dest_clause}\n"
        "Set data_source to 'ai_estimated'."
    )

    result = generate_structured(
        prompt=prompt,
        response_schema=DestinationAgentOutput,
        system_instruction=SYSTEM_INSTRUCTION,
    )
    result.data_source = "ai_estimated"
    return result