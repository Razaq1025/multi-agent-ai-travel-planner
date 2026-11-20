from utils.llm import generate_structured
from utils.schemas import TripRequest, WeatherSummary


SYSTEM_INSTRUCTION = (
    "You are a Weather & Travel Risk Specialist Agent. "
    "Provide realistic seasonal weather expectations, temperature ranges in Celsius, "
    "practical packing/safety advisories, and concrete indoor backup activities. "
    "Never claim historical/seasonal estimates are live forecasts; set data_source to 'ai_estimated'."
)


def run_weather_agent(request: TripRequest, resolved_destination: str) -> WeatherSummary:
    """
    Generates seasonal weather guidance and indoor backup options for the resolved destination.
    """
    month_info = request.travel_month or "upcoming travel dates (general seasonal overview)"

    prompt = (
        f"Destination: {resolved_destination}\n"
        f"Travel Month / Period: {month_info}\n"
        f"Trip Duration: {request.days} days\n"
        f"Traveller Interests: {', '.join(request.interests)}\n\n"
        "Provide expected weather conditions, temperature range in °C, a travel advisory, "
        "and 3-4 specific indoor backup ideas in case of rain or extreme heat. "
        "Set data_source to 'ai_estimated'."
    )

    result = generate_structured(
        prompt=prompt,
        response_schema=WeatherSummary,
        system_instruction=SYSTEM_INSTRUCTION,
    )
    result.data_source = "ai_estimated"
    return result