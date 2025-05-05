"""Pydantic models for place and location data structures."""
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel,Field
from models.chat import Message,Location

class Availability(str, Enum):
    """Enum for availability status"""
    TRUE = "TRUE"
    FALSE = "FALSE"
    NOT_AVAILABLE = "NOT_AVAILABLE"

class PriceRange(BaseModel):
    """ Price range for location """
    startPrice: Optional[str] = None
    endPrice: Optional[str] = None

class Place(BaseModel):
    """ Place data structure that is used for AI ranking """
    id: str
    displayName: str
    location: Optional[Location] = None
    rating: Optional[float] = None
    userRatingCount: Optional[float] = None
    types: List[str] = []
    currentOpeningHours: List[str] = []
    goodForChildren: Optional[Availability] = Availability.NOT_AVAILABLE
    goodForGroups: Optional[Availability] = Availability.NOT_AVAILABLE
    liveMusic: Optional[Availability] = Availability.NOT_AVAILABLE
    allowedDogs: Optional[Availability] = Availability.NOT_AVAILABLE
    outdoorSeating: Optional[Availability] = Availability.NOT_AVAILABLE
    parkingOptions: Optional[Availability] = Availability.NOT_AVAILABLE
    dineIn: Optional[Availability] = Availability.NOT_AVAILABLE
    delivery: Optional[Availability] = Availability.NOT_AVAILABLE
    reservable: Optional[Availability] = Availability.NOT_AVAILABLE
    priceLevel: Optional[str] = None
    priceRange: Optional[PriceRange] = None

class PlaceFullResponse(Place):
    """ Place data structure that is retrieved on API call"""
    formattedAddress: Optional[str] = None
    googleMapsUri: str
    websiteUri: Optional[str] = None
    photos: List[str] = []
    internationalPhoneNumber: Optional[str] = None
    businessStatus: Optional[str] = None

class PlaceRanking(BaseModel):
    """Ranking scores for each Place attribute."""
    id: str
    displayName: float = Field(ge=-1, le=1.0)
    location: float = Field(ge=-1, le=1.0)
    rating: float = Field(ge=-1, le=1.0)
    rating_count: float = Field(ge=-1, le=1.0)
    types: float = Field(ge=-1, le=1.0)
    currentOpeningHours: float = Field(ge=-1, le=1.0)
    goodForChildren: float = Field(ge=-1, le=1.0)
    goodForGroups: float = Field(ge=-1, le=1.0)
    liveMusic: float = Field(ge=-1, le=1.0)
    allowedDogs: float = Field(ge=-1, le=1.0)
    outdoorSeating: float = Field(ge=-1, le=1.0)
    parkingOptions: float = Field(ge=-1, le=1.0)
    dineIn: float = Field(ge=-1, le=1.0)
    delivery: float = Field(ge=-1, le=1.0)
    reservable: float = Field(ge=-1, le=1.0)
    priceLevel: float = Field(ge=-1, le=1.0)
    priceRange: float = Field(ge=-1, le=1.0)

class UserPreferences(BaseModel):
    """ User Preferences for a place """
    place_id: str
    score: float = Field(ge=-1, le=1.0)

class SearchRequest(BaseModel):
    """ Search request data structure. """
    queries: List[str]
    messages: List[Message]
    location: Location
    searchRadius: int

class SearchQueries(BaseModel):
    """ Search queries data structure. """
    queries: List[str] = Field(min_items=1, max_items=3)


class SearchResponse(BaseModel):
    """ Search response data structure. """
    places: List[PlaceFullResponse]
    justification: str
    user_preferences: List[UserPreferences]
