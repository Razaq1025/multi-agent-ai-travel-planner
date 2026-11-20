from typing import List
from services.budget_engine import validate_estimated_expenses
from utils.schemas import (
    AccommodationAgentOutput,
    BudgetAllocation,
    ItineraryAgentOutput,
    ReviewReport,
    TransportAgentOutput,
    TripRequest,
)


def run_review_agent(
    request: TripRequest,
    allocation: BudgetAllocation,
    transport: TransportAgentOutput,
    accommodation: AccommodationAgentOutput,
    itinerary: ItineraryAgentOutput,
) -> ReviewReport:
    """
    Deterministically validates budget constraints, day counts, and schedule feasibility
    across all specialized agent outputs.
    """
    issues: List[str] = []
    suggestions: List[str] = []

    # 1. Extract chosen transport and accommodation costs safely
    t_idx = min(transport.recommended_option_index, len(transport.options) - 1) if transport.options else 0
    transport_cost = transport.options[t_idx].estimated_total_cost if transport.options else 0.0

    a_idx = min(accommodation.recommended_option_index, len(accommodation.options) - 1) if accommodation.options else 0
    accommodation_cost = accommodation.options[a_idx].estimated_total_cost if accommodation.options else 0.0

    # 2. Sum daily itinerary costs (food + activities)
    daily_sum = round(sum(day.estimated_day_cost for day in itinerary.days), 2)

    # Split daily_sum proportionally between Food (65%) and Activities (35%) for reconciliation
    food_est = round(daily_sum * 0.65, 2)
    activities_est = round(daily_sum - food_est, 2)

    expense_check = validate_estimated_expenses(
        allocation=allocation,
        transport_cost=transport_cost,
        accommodation_cost=accommodation_cost,
        food_cost=food_est,
        activities_cost=activities_est,
    )

    if expense_check["within_budget"]:
        budget_status = (
            f"Within budget: ₹{expense_check['total_estimated_cost']:,.2f} estimated vs. "
            f"₹{expense_check['spendable_budget']:,.2f} spendable budget "
            f"(₹{expense_check['remaining_or_overrun']:,.2f} buffer remaining)."
        )
    else:
        overrun = abs(float(expense_check["remaining_or_overrun"]))
        budget_status = (
            f"Budget overrun of ₹{overrun:,.2f}: ₹{expense_check['total_estimated_cost']:,.2f} "
            f"estimated vs. ₹{expense_check['spendable_budget']:,.2f} spendable budget."
        )
        issues.append(budget_status)
        suggestions.append(
            f"Reduce combined accommodation, transport, or daily activity expenses by at least ₹{overrun:,.2f}."
        )

    # 3. Validate itinerary day count & daily hours
    if len(itinerary.days) != request.days:
        msg = f"Itinerary generated {len(itinerary.days)} days instead of requested {request.days} days."
        issues.append(msg)
        suggestions.append(f"Ensure exact {request.days}-day schedule coverage.")

    overpacked_days = []
    for day in itinerary.days:
        total_hours = sum(act.estimated_duration_hours for act in day.activities)
        if total_hours > 11.0:
            overpacked_days.append(f"Day {day.day} ({total_hours:.1f} hrs)")

    if overpacked_days:
        schedule_status = f"Heavy schedule detected on: {', '.join(overpacked_days)}."
        issues.append(schedule_status)
        suggestions.append("Keep planned sightseeing under 10 hours per day to allow transit and rest.")
    else:
        schedule_status = f"Feasible {len(itinerary.days)}-day schedule with balanced daily pacing."

    return ReviewReport(
        is_approved=len(issues) == 0,
        budget_status=budget_status,
        schedule_status=schedule_status,
        issues_found=issues,
        suggestions=suggestions,
    )