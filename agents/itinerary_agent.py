from utils.llm import generate_structured
from utils.schemas import (
    BudgetAllocation,
    ItineraryAgentOutput,
    TripRequest,
    WeatherSummary,
)


SYSTEM_INSTRUCTION = (
    "You are an Activity, Culinary, and Geographic Itinerary Specialist Agent. "
    "Design practical, chronologically ordered day-by-day travel schedules. "
    "CRITICAL RULES:\n"
    "1. Cluster each day's activities within ONE geographic zone/area so travellers do not waste hours zig-zagging.\n"
    "2. Balance Morning, Afternoon, and Evening slots with realistic durations (1.5 to 3.5 hours per activity).\n"
    "3. Include local restaurant/cuisine recommendations matching dietary preferences.\n"
    "4. Keep daily activity + food costs within the allocated Activities + Food budget.\n"
    "5. Set data_source to 'ai_estimated'."
)


def _get_category_budget(allocation: BudgetAllocation, category_name: str) -> float:
    for item in allocation.categories:
        if item.category.lower() == category_name.lower():
            return item.allocated_amount
    return 0.0


def run_itinerary_agent(
    request: TripRequest,
    resolved_destination: str,
    allocation: BudgetAllocation,
    weather: WeatherSummary,
    feedback: str = "",
) -> ItineraryAgentOutput:
    """
    Generates a geographically clustered day-by-day itinerary with local food picks
    and per-day cost estimates.
    """
    food_budget = _get_category_budget(allocation, "Food")
    activities_budget = _get_category_budget(allocation, "Activities")
    combined_daily_budget = round((food_budget + activities_budget) / request.days, 2)
    feedback_clause = f"\nReviewer Replanning Feedback to Address: {feedback}\n" if feedback else ""

    prompt = (
        f"Destination: {resolved_destination}\n"
        f"Duration: {request.days} days\n"
        f"Travellers: {request.travellers}\n"
        f"Interests: {', '.join(request.interests)}\n"
        f"Dietary Preferences: {request.dietary_preferences}\n"
        f"Weather Context: {weather.expected_condition} ({weather.temperature_range_c})\n"
        f"Allocated Food Budget: ₹{food_budget:,.2f} | Allocated Activities Budget: ₹{activities_budget:,.2f} "
        f"(approx. ₹{combined_daily_budget:,.2f}/day total for food + activities)\n"
        f"{feedback_clause}\n"
        f"Generate a complete {request.days}-day itinerary. Each day must focus on a specific geographic zone "
        "(`area_focus`), include Morning, Afternoon, and Evening activities, 2-3 local restaurant/food spots, "
        "and a realistic `estimated_day_cost` (food + entry fees for all travellers). "
        "Set data_source to 'ai_estimated'."
    )

    result = generate_structured(
        prompt=prompt,
        response_schema=ItineraryAgentOutput,
        system_instruction=SYSTEM_INSTRUCTION,
    )
    result.data_source = "ai_estimated"
    return result


def refine_itinerary(
    request: TripRequest,
    resolved_destination: str,
    allocation: BudgetAllocation,
    current_itinerary: ItineraryAgentOutput,
    modification_instruction: str,
) -> ItineraryAgentOutput:
    """
    Modifies an existing day-wise itinerary based on user feedback while preserving
    budget constraints and geographic clustering.
    """
    food_budget = _get_category_budget(allocation, "Food")
    activities_budget = _get_category_budget(allocation, "Activities")
    total_allowed = round(food_budget + activities_budget, 2)

    prompt = (
        f"Destination: {resolved_destination}\n"
        f"Duration: {request.days} days | Travellers: {request.travellers}\n"
        f"Dietary Preferences: {request.dietary_preferences}\n"
        f"Combined Food + Activities Budget Ceiling: ₹{total_allowed:,.2f}\n\n"
        f"CURRENT ITINERARY (JSON):\n{current_itinerary.model_dump_json(indent=2)}\n\n"
        f"USER MODIFICATION REQUEST:\n{modification_instruction}\n\n"
        "Update the itinerary to satisfy the user's modification request while keeping "
        "unchanged days intact, preserving geographic clustering per day, and staying within "
        "the budget ceiling. Set data_source to 'ai_estimated'."
    )

    result = generate_structured(
        prompt=prompt,
        response_schema=ItineraryAgentOutput,
        system_instruction=SYSTEM_INSTRUCTION,
    )
    result.data_source = "ai_estimated"
    return result