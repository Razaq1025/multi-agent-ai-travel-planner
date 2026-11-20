import pandas as pd
import streamlit as st
from pydantic import ValidationError

from services.langgraph_planner import run_multi_agent_planner
from utils.schemas import TripRequest


st.set_page_config(
    page_title="Multi-Agent AI Travel Planner",
    page_icon="✈️",
    layout="wide",
)

st.title("✈️ Multi-Agent AI-Based Personalized Travel Planner")
st.caption(
    "Orchestrated with LangGraph & Google Gemini • Deterministic Financial Engine • "
    "Transparent Data Provenance (AI-Estimated vs. Deterministic)"
)

st.divider()

with st.form("travel_planner_form"):
    st.subheader("1. Trip Basics & Budget")
    col1, col2, col3 = st.columns(3)

    with col1:
        starting_location = st.text_input(
            "Starting Location *",
            placeholder="e.g. Visakhapatnam",
        )
        destination = st.text_input(
            "Preferred Destination (Optional)",
            placeholder="Leave blank to let Destination Agent recommend",
        )

    with col2:
        days = st.number_input("Number of Days *", min_value=1, max_value=30, value=4)
        travellers = st.number_input("Number of Travellers *", min_value=1, max_value=20, value=2)

    with col3:
        total_budget = st.number_input(
            "Total Budget (₹ INR) *",
            min_value=1000,
            value=25000,
            step=1000,
        )
        travel_month = st.selectbox(
            "Travel Month",
            [
                "Flexible",
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ],
            index=11,
        )

    st.subheader("2. Preferences & Constraints")
    pcol1, pcol2, pcol3 = st.columns(3)

    with pcol1:
        interests = st.multiselect(
            "Travel Interests *",
            [
                "Beaches",
                "Adventure",
                "Nature",
                "Historical Places",
                "Food",
                "Shopping",
                "Sightseeing",
                "Spiritual & Culture",
            ],
            default=["Beaches", "Historical Places", "Food"],
        )

    with pcol2:
        transport_preference = st.selectbox(
            "Preferred Transportation",
            ["Any", "Train", "Flight", "Bus", "Road / Car"],
        )
        accommodation_preference = st.selectbox(
            "Accommodation Tier",
            ["Budget", "Mid-range", "Luxury"],
            index=1,
        )

    with pcol3:
        dietary_preferences = st.selectbox(
            "Dietary Preferences",
            ["No restrictions", "Vegetarian", "Vegan", "Halal", "Jain", "Seafood Lover"],
        )
        additional_notes = st.text_input(
            "Additional Requirements",
            placeholder="e.g. Avoid hectic mornings, kid-friendly, beachside stay",
        )

    submitted = st.form_submit_button("🚀 Generate Multi-Agent Travel Plan", width="stretch")


if submitted:
    if not starting_location.strip():
        st.error("Please enter your starting location.")
    elif not interests:
        st.error("Please select at least one travel interest.")
    else:
        try:
            trip_request = TripRequest(
                starting_location=starting_location.strip(),
                destination=destination.strip() if destination.strip() else None,
                days=int(days),
                travellers=int(travellers),
                total_budget=float(total_budget),
                interests=interests,
                transport_preference=transport_preference,
                accommodation_preference=accommodation_preference,
                travel_month=None if travel_month == "Flexible" else travel_month,
                dietary_preferences=dietary_preferences,
                additional_notes=additional_notes.strip(),
            )
        except ValidationError as ve:
            st.error(f"Input validation error: {ve}")
            st.stop()

        with st.spinner("Coordinating specialized AI agents via LangGraph..."):
            result = run_multi_agent_planner(trip_request)

        st.success(f"Personalized travel plan ready for **{result['resolved_destination']}**!")

        # Multi-Agent Execution Trace & Review Status
        with st.expander("🧠 Multi-Agent LangGraph Execution Trace & Validation Report", expanded=False):
            for step in result["execution_trace"]:
                st.write(f"✅ {step}")
            review = result["review_report"]
            st.info(f"**Budget Validation:** {review.budget_status}")
            st.info(f"**Schedule Validation:** {review.schedule_status}")

        # Top KPI Summary
        expense = result["expense_summary"]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Primary Destination", result["resolved_destination"])
        m2.metric("Duration & Group", f"{trip_request.days}D / {trip_request.travellers} Pax")
        m3.metric("Total Budget", f"₹{trip_request.total_budget:,.0f}")
        m4.metric(
            "Estimated Trip Cost",
            f"₹{expense['total_estimated_cost']:,.0f}",
            delta=f"₹{expense['remaining_or_overrun']:,.0f} buffer"
            if expense["within_budget"]
            else f"-₹{abs(expense['remaining_or_overrun']):,.0f} overrun",
        )

        st.divider()

        tab_itin, tab_budget, tab_stay_travel, tab_dest_weather = st.tabs(
            [
                "🗓️ Day-wise Itinerary & Food",
                "💰 Budget Breakdown & Expenses",
                "🚆 Transport & Accommodation",
                "🌍 Destinations & Weather",
            ]
        )

        # TAB 1: Day-wise Itinerary & Food
        with tab_itin:
            itin_out = result["itinerary_output"]
            st.caption(f"Data Source: `{itin_out.data_source}` (Geographically clustered per day)")
            for day in itin_out.days:
                with st.expander(
                    f"Day {day.day}: {day.theme} — Zone: {day.area_focus} (Est. ₹{day.estimated_day_cost:,.0f})",
                    expanded=True,
                ):
                    for act in day.activities:
                        st.markdown(
                            f"**{act.time_slot} — {act.place_name}** ({act.area}) • "
                            f"⏱️ {act.estimated_duration_hours} hrs • 💵 Est. ₹{act.estimated_cost_total:,.0f}"
                        )
                        st.write(act.description)
                    if day.recommended_restaurants:
                        st.markdown(
                            "🍽️ **Recommended Restaurants & Local Food:** "
                            + ", ".join(day.recommended_restaurants)
                        )

            if itin_out.overall_tips:
                st.subheader("💡 Smart Travel Tips")
                for tip in itin_out.overall_tips:
                    st.write(f"- {tip}")

        # TAB 2: Budget Allocation & Expense Reconciliation
        with tab_budget:
            alloc = result["budget_allocation"]
            st.caption(f"Data Source: `{alloc.data_source}` (Exact financial reconciliation)")

            for warn in alloc.warnings:
                st.warning(warn)

            budget_rows = [
                {
                    "Category": c.category,
                    "Share (%)": f"{c.percentage:.1f}%",
                    "Allocated Total (₹)": f"₹{c.allocated_amount:,.2f}",
                    "Per Person (₹)": f"₹{c.per_person_amount:,.2f}",
                    "Coverage Notes": c.notes,
                }
                for c in alloc.categories
            ]
            st.dataframe(pd.DataFrame(budget_rows), width="stretch", hide_index=True)

            st.subheader("Estimated Expense Reconciliation")
            st.write(f"- **Total User Budget:** ₹{alloc.total_budget:,.2f}")
            st.write(f"- **Spendable Budget (Excl. 5% Emergency Reserve):** ₹{expense['spendable_budget']:,.2f}")
            st.write(f"- **Agent-Estimated Total Cost:** ₹{expense['total_estimated_cost']:,.2f}")
            st.write(f"- **Remaining Buffer / Overrun:** ₹{expense['remaining_or_overrun']:,.2f}")

        # TAB 3: Transportation & Accommodation
        with tab_stay_travel:
            trans = result["transport_output"]
            accom = result["accommodation_output"]

            st.subheader("🚆 Transportation Options")
            st.caption(f"Data Source: `{trans.data_source}` (Estimated fares, not live booking quotes)")
            for idx, opt in enumerate(trans.options):
                badge = " ⭐ Recommended" if idx == trans.recommended_option_index else ""
                with st.container(border=True):
                    st.markdown(f"**{opt.mode} — {opt.operator_or_route}**{badge}")
                    st.write(
                        f"⏱️ Duration: **{opt.estimated_duration}** | "
                        f"💵 Est. Total ({trip_request.travellers} pax): **₹{opt.estimated_total_cost:,.0f}**"
                    )
                    st.write(f"Why it fits: {opt.pros}")

            st.subheader("🏨 Accommodation Recommendations")
            st.caption(f"Data Source: `{accom.data_source}` (Estimated nightly tariffs)")
            for idx, stay in enumerate(accom.options):
                badge = " ⭐ Recommended" if idx == accom.recommended_option_index else ""
                with st.container(border=True):
                    st.markdown(f"**{stay.name}** ({stay.category} • {stay.area}){badge}")
                    st.write(
                        f"🌙 Per Night: **₹{stay.estimated_cost_per_night:,.0f}** | "
                        f"💵 Total Stay: **₹{stay.estimated_total_cost:,.0f}**"
                    )
                    st.write("Highlights: " + ", ".join(stay.highlights))

        # TAB 4: Destinations & Weather
        with tab_dest_weather:
            dest_out = result["destination_output"]
            weather = result["weather_output"]

            st.subheader("🌍 Destination Analysis & Alternatives")
            st.caption(f"Data Source: `{dest_out.data_source}`")
            prim = dest_out.primary_destination
            with st.container(border=True):
                st.markdown(f"### Primary Choice: {prim.name} ({prim.region_or_country})")
                st.write(prim.why_it_fits)
                st.write(
                    f"**Best For:** {', '.join(prim.best_for)} | "
                    f"**Est. Daily Cost/Person:** ₹{prim.estimated_daily_cost_per_person:,.0f}"
                )

            st.markdown("#### Alternative Destinations Within Similar Budget")
            alt_cols = st.columns(max(1, len(dest_out.alternatives)))
            for col, alt in zip(alt_cols, dest_out.alternatives):
                with col:
                    with st.container(border=True):
                        st.markdown(f"**{alt.name}** ({alt.region_or_country})")
                        st.write(alt.why_it_fits)
                        st.caption(f"Est. ₹{alt.estimated_daily_cost_per_person:,.0f}/person/day")

            st.divider()
            st.subheader("🌦️ Seasonal Weather & Indoor Backups")
            st.caption(f"Data Source: `{weather.data_source}`")
            st.write(f"**Expected Conditions:** {weather.expected_condition}")
            st.write(f"**Temperature Range:** {weather.temperature_range_c}")
            st.info(f"**Advisory:** {weather.travel_advisory}")
            st.markdown("**Indoor Backup Alternatives:**")
            for idea in weather.indoor_backup_ideas:
                st.write(f"- {idea}")