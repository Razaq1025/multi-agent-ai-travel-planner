from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder

from database.storage import list_recent_trips, save_trip_plan
from services.langgraph_planner import run_multi_agent_planner
from utils.schemas import TripRequest


app = FastAPI(
    title="Multi-Agent AI Personalized Travel Planner API",
    description="REST API powered by LangGraph, Google Gemini, Deterministic Budget Engine, and Google OR-Tools.",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "multi-agent-travel-planner"}


@app.post("/api/plan")
def create_travel_plan(request: TripRequest):
    try:
        result = run_multi_agent_planner(request)
        trip_id = save_trip_plan(result)
        encoded = jsonable_encoder(result)
        encoded["trip_id"] = trip_id
        return encoded
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/trips")
def get_saved_trips(limit: int = 10):
    return {"trips": list_recent_trips(limit=limit)}