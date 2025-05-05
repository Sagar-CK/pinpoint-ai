"""Pydantic models for place and location data structures."""
from typing import Optional, List
from models.chat import Message
from pydantic import BaseModel

class Location(BaseModel):
    """ Place location data structure. """
    latitude: float
    longitude: float

class Place(BaseModel):
    """ Place data structure. """
    displayName: str
    formattedAddress: str
    rating: float
    googleMapsUri: str
    websiteUri: Optional[str] = None
    location: Location

class SearchRequest(BaseModel):
    """ Search request data structure. """
    query: str
    messages: List[Message]

class SearchResponse(BaseModel):
    """ Search response data structure. """
    places: List[Place]
    justification: str
