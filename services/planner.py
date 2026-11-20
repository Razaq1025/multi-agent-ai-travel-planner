
def generate_budget(budget):
    """
    Divide the user's total budget into categories.
    These are planning allocations, not live prices.
    """

    return {
        "Transportation": budget * 0.30,
        "Accommodation": budget * 0.35,
        "Food": budget * 0.20,
        "Activities": budget * 0.10,
        "Emergency": budget * 0.05
    }


def generate_itinerary(destination, days, interests):
    """
    Generate a basic day-wise travel itinerary.
    """

    activities = [
        "Explore popular local attractions",
        "Experience local food and culture",
        "Explore scenic places and sightseeing",
        "Enjoy activities based on your interests",
        "Relax and explore nearby attractions",
        "Visit local markets and shopping areas"
    ]

    itinerary = []

    for day in range(1, days + 1):

        activity = activities[(day - 1) % len(activities)]

        itinerary.append({
            "day": day,
            "destination": destination,
            "morning": activity,
            "afternoon": f"Explore {', '.join(interests)}",
            "evening": "Enjoy the local atmosphere and dinner"
        })

    return itinerary


def generate_travel_plan(
    starting_location,
    destination,
    days,
    travellers,
    budget,
    interests
):
    """
    Main function that combines budget and itinerary.
    """

    budget_breakdown = generate_budget(budget)

    itinerary = generate_itinerary(
        destination,
        days,
        interests
    )

    return {
        "starting_location": starting_location,
        "destination": destination,
        "days": days,
        "travellers": travellers,
        "total_budget": budget,
        "budget_breakdown": budget_breakdown,
        "itinerary": itinerary
    }
