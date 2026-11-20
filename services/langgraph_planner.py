from typing import Any, Dict, List, Optional, TypedDict
from langgraph.graph import END, StateGraph

from agents.accommodation_agent import run_accommodation_agent
from agents.destination_agent import run_destination_agent
from agents.itinerary_agent import run_itinerary_agent
from agents.review_agent import run_review_agent
from agents.transport_agent import run_transport_agent
from agents.weather_agent import run_weather_agent
from services.budget_engine import allocate_budget, validate_estimated_expenses
from utils.schemas import (
    AccommodationAgentOutput,
    BudgetAllocation,
    DestinationAgentOutput,
    ItineraryAgentOutput,
    ReviewReport,
    TransportAgentOutput,
    TripRequest,
    WeatherSummary,
)


class TravelGraphState(TypedDict):
    request: TripRequest
    resolved_destination: str
    budget_allocation: Optional[BudgetAllocation]
    destination_output: Optional[DestinationAgentOutput]
    weather_output: Optional[WeatherSummary]
    transport_output: Optional[TransportAgentOutput]
    accommodation_output: Optional[AccommodationAgentOutput]
    itinerary_output: Optional[ItineraryAgentOutput]
    review_report: Optional[ReviewReport]
    revision_count: int
    replan_feedback: str
    execution_trace: List[str]


def budget_node(state: TravelGraphState) -> Dict[str, Any]:
    allocation = allocate_budget(state["request"])
    trace = list(state.get("execution_trace", []))
    trace.append("Budget Engine: Allocated deterministic category budgets.")
    return {"budget_allocation": allocation, "execution_trace": trace}


def destination_node(state: TravelGraphState) -> Dict[str, Any]:
    dest_out = run_destination_agent(state["request"])
    resolved = dest_out.primary_destination.name
    trace = list(state.get("execution_trace", []))
    trace.append(f"Destination Agent: Resolved primary destination -> {resolved}.")
    return {
        "destination_output": dest_out,
        "resolved_destination": resolved,
        "execution_trace": trace,
    }


def weather_node(state: TravelGraphState) -> Dict[str, Any]:
    weather_out = run_weather_agent(state["request"], state["resolved_destination"])
    trace = list(state.get("execution_trace", []))
    trace.append("Weather Agent: Analyzed seasonal forecast & indoor backups.")
    return {"weather_output": weather_out, "execution_trace": trace}


def transport_node(state: TravelGraphState) -> Dict[str, Any]:
    transport_out = run_transport_agent(
        request=state["request"],
        resolved_destination=state["resolved_destination"],
        allocation=state["budget_allocation"],
        feedback=state.get("replan_feedback", ""),
    )
    trace = list(state.get("execution_trace", []))
    trace.append("Transportation Agent: Evaluated intercity travel options.")
    return {"transport_output": transport_out, "execution_trace": trace}


def accommodation_node(state: TravelGraphState) -> Dict[str, Any]:
    accom_out = run_accommodation_agent(
        request=state["request"],
        resolved_destination=state["resolved_destination"],
        allocation=state["budget_allocation"],
        feedback=state.get("replan_feedback", ""),
    )
    trace = list(state.get("execution_trace", []))
    trace.append("Accommodation Agent: Selected stay recommendations.")
    return {"accommodation_output": accom_out, "execution_trace": trace}


def itinerary_node(state: TravelGraphState) -> Dict[str, Any]:
    itin_out = run_itinerary_agent(
        request=state["request"],
        resolved_destination=state["resolved_destination"],
        allocation=state["budget_allocation"],
        weather=state["weather_output"],
        feedback=state.get("replan_feedback", ""),
    )
    trace = list(state.get("execution_trace", []))
    trace.append("Itinerary Agent: Built geographically clustered day-wise schedule & food picks.")
    return {"itinerary_output": itin_out, "execution_trace": trace}


def review_node(state: TravelGraphState) -> Dict[str, Any]:
    report = run_review_agent(
        request=state["request"],
        allocation=state["budget_allocation"],
        transport=state["transport_output"],
        accommodation=state["accommodation_output"],
        itinerary=state["itinerary_output"],
    )
    rev_count = state.get("revision_count", 0)
    trace = list(state.get("execution_trace", []))

    if report.is_approved:
        trace.append("Review Agent: Plan validated and approved.")
        return {"review_report": report, "execution_trace": trace}

    feedback = " | ".join(report.suggestions)
    trace.append(f"Review Agent: Flagged issues ({'; '.join(report.issues_found)}).")
    return {
        "review_report": report,
        "revision_count": rev_count + 1,
        "replan_feedback": feedback,
        "execution_trace": trace,
    }


def route_after_review(state: TravelGraphState) -> str:
    report = state.get("review_report")
    if report and not report.is_approved and state.get("revision_count", 0) <= 1:
        return "replan_itinerary"
    return "approve"


def build_travel_graph():
    workflow = StateGraph(TravelGraphState)

    workflow.add_node("budget", budget_node)
    workflow.add_node("destination", destination_node)
    workflow.add_node("weather", weather_node)
    workflow.add_node("transport", transport_node)
    workflow.add_node("accommodation", accommodation_node)
    workflow.add_node("itinerary", itinerary_node)
    workflow.add_node("review", review_node)

    workflow.set_entry_point("budget")
    workflow.add_edge("budget", "destination")
    workflow.add_edge("destination", "weather")
    workflow.add_edge("weather", "transport")
    workflow.add_edge("transport", "accommodation")
    workflow.add_edge("accommodation", "itinerary")
    workflow.add_edge("itinerary", "review")

    workflow.add_conditional_edges(
        "review",
        route_after_review,
        {
            "replan_itinerary": "itinerary",
            "approve": END,
        },
    )

    return workflow.compile()


def run_multi_agent_planner(request: TripRequest) -> Dict[str, Any]:
    """
    Executes the full LangGraph multi-agent travel planning pipeline and returns
    a unified structured dictionary including expense reconciliation.
    """
    graph = build_travel_graph()
    initial_state: TravelGraphState = {
        "request": request,
        "resolved_destination": request.destination or "",
        "budget_allocation": None,
        "destination_output": None,
        "weather_output": None,
        "transport_output": None,
        "accommodation_output": None,
        "itinerary_output": None,
        "review_report": None,
        "revision_count": 0,
        "replan_feedback": "",
        "execution_trace": [],
    }

    final_state = graph.invoke(initial_state)

    allocation = final_state["budget_allocation"]
    transport = final_state["transport_output"]
    accommodation = final_state["accommodation_output"]
    itinerary = final_state["itinerary_output"]

    t_idx = min(transport.recommended_option_index, len(transport.options) - 1) if transport.options else 0
    a_idx = min(accommodation.recommended_option_index, len(accommodation.options) - 1) if accommodation.options else 0

    transport_cost = transport.options[t_idx].estimated_total_cost if transport.options else 0.0
    accommodation_cost = accommodation.options[a_idx].estimated_total_cost if accommodation.options else 0.0
    daily_sum = round(sum(d.estimated_day_cost for d in itinerary.days), 2)
    food_est = round(daily_sum * 0.65, 2)
    activities_est = round(daily_sum - food_est, 2)

    expense_summary = validate_estimated_expenses(
        allocation=allocation,
        transport_cost=transport_cost,
        accommodation_cost=accommodation_cost,
        food_cost=food_est,
        activities_cost=activities_est,
    )

    return {
        "request": request,
        "resolved_destination": final_state["resolved_destination"],
        "budget_allocation": allocation,
        "destination_output": final_state["destination_output"],
        "weather_output": final_state["weather_output"],
        "transport_output": transport,
        "accommodation_output": accommodation,
        "itinerary_output": itinerary,
        "review_report": final_state["review_report"],
        "expense_summary": expense_summary,
        "execution_trace": final_state["execution_trace"],
    }