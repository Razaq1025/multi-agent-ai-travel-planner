from services.external_apis import fetch_weather_data
from utils.llm import generate_structured
from utils.schemas import TripRequest, WeatherSummary


SYSTEM_INSTRUCTION = (
    "You are a Weather & Travel Risk Specialist Agent. "
    "Using the provided weather feed context, deliver realistic weather expectations, "
    "temperature ranges in Celsius, practical packing/safety advisories, and concrete "
    "indoor backup activities. Preserve the exact data_source passed in the prompt."
)


def run_weather_agent(request: TripRequest, resolved_destination: str) -> WeatherSummary:
    """
    Retrieves weather feed data (live OpenWeatherMap if configured, else mock_api)
    and synthesizes travel advisories + indoor backup alternatives.
    """
    month_info = request.travel_month or "upcoming travel dates (general seasonal overview)"
    feed = fetch_weather_data(resolved_destination, request.travel_month)
    source_tag = feed["data_source"]

    prompt = (
        f"Destination: {resolved_destination}\n"
        f"Travel Month / Period: {month_info}\n"
        f"Trip Duration: {request.days} days\n"
        f"Traveller Interests: {', '.join(request.interests)}\n"
        f"External Weather Feed ({feed['provider']}): {feed['summary']} | "
        f"Range: {feed['temperature_range_c']}\n\n"
        "Provide expected weather conditions, temperature range in °C, a travel advisory, "
        "and 3-4 specific indoor backup ideas in case of rain or extreme heat. "
        f"Set data_source to '{source_tag}'."
    )

    result = generate_structured(
        prompt=prompt,
        response_schema=WeatherSummary,
        system_instruction=SYSTEM_INSTRUCTION,
    )
    result.data_source = source_tag
    return result