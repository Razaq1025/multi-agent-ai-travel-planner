import os
from typing import Any, Dict, List
import requests
from dotenv import load_dotenv

load_dotenv(override=True)


def fetch_weather_data(destination: str, travel_month: str | None = None) -> Dict[str, Any]:
    """
    Fetches live current/forecast weather from OpenWeatherMap if OPENWEATHER_API_KEY is set.
    Otherwise returns a clearly labeled 'mock_api' fallback payload so the Weather Agent
    can combine grounded context with seasonal reasoning.
    """
    api_key = (os.getenv("OPENWEATHER_API_KEY") or "").strip()

    if api_key:
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {"q": destination, "appid": api_key, "units": "metric"}
            resp = requests.get(url, params=params, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                weather_desc = data["weather"][0]["description"].capitalize()
                temp = data["main"]["temp"]
                temp_min = data["main"]["temp_min"]
                temp_max = data["main"]["temp_max"]
                humidity = data["main"]["humidity"]
                return {
                    "data_source": "live_api",
                    "provider": "OpenWeatherMap",
                    "summary": f"{weather_desc}, {temp}°C (Humidity: {humidity}%)",
                    "temperature_range_c": f"{temp_min}°C to {temp_max}°C",
                    "raw_condition": weather_desc,
                }
        except Exception:
            # Fall back cleanly to mock_api if network/API fails
            pass

    return {
        "data_source": "mock_api",
        "provider": "Simulated Seasonal Weather Feed (No OPENWEATHER_API_KEY configured)",
        "summary": f"Seasonal baseline lookup for {destination} ({travel_month or 'General Season'})",
        "temperature_range_c": "22°C to 31°C",
        "raw_condition": "Partly sunny / moderate seasonal conditions",
    }


def fetch_place_coordinates(destination: str, place_names: List[str]) -> Dict[str, Any]:
    """
    Resolves (latitude, longitude) coordinates for attractions using Google Places Text Search
    if GOOGLE_MAPS_API_KEY is configured; otherwise returns deterministic mock coordinates
    around the destination center for OR-Tools route optimization.
    """
    api_key = (os.getenv("GOOGLE_MAPS_API_KEY") or "").strip()
    resolved_places: List[Dict[str, Any]] = []

    if api_key:
        try:
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            for name in place_names:
                resp = requests.get(
                    url,
                    params={"query": f"{name}, {destination}", "key": api_key},
                    timeout=6,
                )
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    if results:
                        loc = results[0]["geometry"]["location"]
                        resolved_places.append(
                            {
                                "name": name,
                                "lat": float(loc["lat"]),
                                "lng": float(loc["lng"]),
                                "formatted_address": results[0].get("formatted_address", destination),
                            }
                        )
            if len(resolved_places) == len(place_names) and place_names:
                return {
                    "data_source": "live_api",
                    "provider": "Google Places API",
                    "places": resolved_places,
                }
        except Exception:
            pass

    # Deterministic mock coordinates spread realistically (~2-8 km apart) for OR-Tools testing
    base_lat, base_lng = 15.4909, 73.8278
    for idx, name in enumerate(place_names):
        offset_lat = ((idx * 37) % 11 - 5) * 0.015
        offset_lng = ((idx * 53) % 11 - 5) * 0.015
        resolved_places.append(
            {
                "name": name,
                "lat": round(base_lat + offset_lat, 5),
                "lng": round(base_lng + offset_lng, 5),
                "formatted_address": f"{name} Zone, {destination} (Simulated Coordinates)",
            }
        )

    return {
        "data_source": "mock_api",
        "provider": "Simulated Spatial Coordinate Resolver (No GOOGLE_MAPS_API_KEY configured)",
        "places": resolved_places,
    }