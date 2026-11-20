# Multi-Agent AI-Based Personalized Travel Planner

A final-year B.Tech CSE (AI & ML) project implementing a hybrid **Multi-Agent AI + Deterministic Optimization** travel planning system powered by **LangGraph**, **Google Gemini**, **Google OR-Tools**, **FastAPI**, and **Streamlit**.

---

## System Architecture

Instead of relying on a single monolithic LLM prompt, the planner coordinates specialized domain agents over a shared typed workflow state (`TravelGraphState`) using **LangGraph (`StateGraph`)**:

1. **Deterministic Budget Engine (`services/budget_engine.py`)**
   - Allocates user budgets across *Transportation*, *Accommodation*, *Food*, *Activities*, and *Emergency Reserve* using tier-aware weights (`Budget`, `Mid-range`, `Luxury`) with exact financial reconciliation.
2. **Destination Specialist Agent (`agents/destination_agent.py`)**
   - Validates user-chosen destinations or discovers best-fit destinations from scratch, plus two budget-compatible alternatives.
3. **Weather & Risk Agent (`agents/weather_agent.py` + `services/external_apis.py`)**
   - Integrates with OpenWeatherMap (`live_api`) when configured, or falls back transparently to `mock_api` seasonal baselines with indoor backup activities.
4. **Transportation Agent (`agents/transport_agent.py`)**
   - Compares realistic intercity transport modes (Train, Flight, Bus, Road) within the allocated transportation ceiling.
5. **Accommodation Agent (`agents/accommodation_agent.py`)**
   - Recommends stays matching the user's tier, group size, number of nights, and accommodation budget.
6. **Itinerary & Culinary Agent (`agents/itinerary_agent.py`)**
   - Generates geographically clustered day-wise schedules with local food picks respecting dietary preferences and supports **interactive itinerary refinement**.
7. **Google OR-Tools Route Optimizer (`services/route_optimizer.py`)**
   - Solves an open Traveling Salesperson Problem (`PATH_CHEAPEST_ARC`) over daily attraction coordinates to minimize intra-day transit distance.
8. **Review & Validation Agent (`agents/review_agent.py`)**
   - Deterministically verifies that estimated expenses stay within spendable budget and schedules remain balanced—triggering conditional replanning in LangGraph if constraints are violated.

---

## Data Provenance Policy

Every output explicitly declares its data provenance so estimated or simulated figures are never misrepresented as live bookings:
- `deterministic_calculation` — Exact Python financial splits & expense reconciliation
- `ai_estimated` — Structured Pydantic outputs generated via Google Gemini
- `live_api` — Live external API responses (OpenWeatherMap / Google Places when keys are configured)
- `mock_api` — Clearly labeled fallback data when optional external API keys are omitted

---

## Project Structure

```text
Multi-Agent-Travel-Planner/
├── agents/                  # Specialized LangGraph worker & review agents
├── backend/                 # FastAPI REST endpoints (/health, /api/plan, /api/trips)
├── database/                # SQLite trip history persistence layer
├── services/                # LangGraph orchestrator, budget engine, OR-Tools optimizer, API connectors
├── tests/                   # Automated pytest suite
├── utils/                   # Pydantic schemas & Gemini structured LLM client
├── app.py                   # Interactive Streamlit web application
├── requirements.txt         # Pinned Python dependencies
└── .env.example             # Environment variable template