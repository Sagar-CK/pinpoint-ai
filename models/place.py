"""Pydantic models for place and location data structures."""
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel
from models.chat import Message

class Availability(str, Enum):
    """Enum for availability status"""
    TRUE = "TRUE"
    FALSE = "FALSE"
    NOT_AVAILABLE = "NOT_AVAILABLE"

class Location(BaseModel):
    """ Place location data structure. """
    latitude: float
    longitude: float

class PriceRange(BaseModel):
    """ Price range for location """
    lower: Optional[str] = None
    upper: Optional[str] = None    

class Place(BaseModel):
    """ Place data structure that is used for AI ranking """
    id: str
    displayName: str
    location: Location
    rating: float
    userRatingCount: float
    types: Optional[List[str]] = []
    currentOpeningHours: Optional[List[str]] = []
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
    formattedAddress: str
    googleMapsUri: str
    websiteUri: Optional[str] = None
    photos: Optional[List[str]] = []
    internationalPhoneNumber: Optional[str] = None
    businessStatus: Optional[str] = None

class PlaceRanking(BaseModel):
    """Ranking scores for each Place attribute."""
    id: str
    displayName: float
    location: float
    rating: float
    rating_count: float
    types: float
    currentOpeningHours: float
    goodForChildren: float
    goodForGroups: float
    liveMusic: float
    allowedDogs: float
    outdoorSeating: float
    parkingOptions: float
    dineIn: float
    delivery: float
    reservable: float
    priceLevel: float
    priceRange: float

class SearchRequest(BaseModel):
    """ Search request data structure. """
    query: str
    messages: List[Message]

class SearchResponse(BaseModel):
    """ Search response data structure. """
    places: List[PlaceFullResponse]
    justification: str

class UserPreferences(BaseModel):
    """ User Preferences for a place """
    place_id: str
    score: float
