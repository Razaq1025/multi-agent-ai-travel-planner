from typing import List, Literal, Optional
from pydantic import BaseModel, Field


DataSourceType = Literal[
    "deterministic_calculation",
    "ai_estimated",
    "mock_api",
    "live_api"
]


class TripRequest(BaseModel):
    starting_location: str = Field(..., min_length=2)
    destination: Optional[str] = Field(default=None)
    days: int = Field(..., ge=1, le=30)
    travellers: int = Field(..., ge=1, le=20)
    total_budget: float = Field(..., gt=0)
    interests: List[str] = Field(default_factory=list)
    transport_preference: str = Field(default="Any")
    accommodation_preference: str = Field(default="Mid-range")
    travel_month: Optional[str] = Field(default=None)
    dietary_preferences: str = Field(default="No restrictions")
    additional_notes: str = Field(default="")


class BudgetCategory(BaseModel):
    category: str
    allocated_amount: float
    percentage: float
    per_person_amount: float
    notes: str


class BudgetAllocation(BaseModel):
    total_budget: float
    currency: str = "INR"
    categories: List[BudgetCategory]
    is_feasible: bool
    warnings: List[str] = Field(default_factory=list)
    data_source: DataSourceType = "deterministic_calculation"


class DestinationRecommendation(BaseModel):
    name: str
    region_or_country: str
    why_it_fits: str
    best_for: List[str]
    estimated_daily_cost_per_person: float


class DestinationAgentOutput(BaseModel):
    primary_destination: DestinationRecommendation
    alternatives: List[DestinationRecommendation]
    data_source: DataSourceType = "ai_estimated"


class TransportOption(BaseModel):
    mode: str
    operator_or_route: str
    estimated_duration: str
    estimated_total_cost: float
    pros: str
    data_source: DataSourceType = "ai_estimated"


class AccommodationOption(BaseModel):
    name: str
    category: str
    area: str
    estimated_cost_per_night: float
    estimated_total_cost: float
    highlights: List[str]
    data_source: DataSourceType = "ai_estimated"


class ActivityItem(BaseModel):
    time_slot: Literal["Morning", "Afternoon", "Evening"]
    place_name: str
    area: str
    description: str
    estimated_duration_hours: float
    estimated_cost_total: float


class DayItinerary(BaseModel):
    day: int
    theme: str
    area_focus: str
    activities: List[ActivityItem]
    recommended_restaurants: List[str]
    estimated_day_cost: float


class WeatherSummary(BaseModel):
    expected_condition: str
    temperature_range_c: str
    travel_advisory: str
    indoor_backup_ideas: List[str]
    data_source: DataSourceType = "ai_estimated"


class ReviewReport(BaseModel):
    is_approved: bool
    budget_status: str
    schedule_status: str
    issues_found: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class TransportAgentOutput(BaseModel):
    options: List[TransportOption]
    recommended_option_index: int = Field(default=0, ge=0)
    data_source: DataSourceType = "ai_estimated"


class AccommodationAgentOutput(BaseModel):
    options: List[AccommodationOption]
    recommended_option_index: int = Field(default=0, ge=0)
    data_source: DataSourceType = "ai_estimated"


class ItineraryAgentOutput(BaseModel):
    days: List[DayItinerary]
    overall_tips: List[str] = Field(default_factory=list)
    data_source: DataSourceType = "ai_estimated"
