""" Chat request data structures. """
from typing import List
from pydantic import BaseModel

class Message(BaseModel):
    """ Message data structure. """
    role: str
    content: str

class Location(BaseModel):
    """ Place location data structure. """
    latitude: float
    longitude: float

class User(BaseModel):
    name: str
    location: Location

class ChatRequest(BaseModel):
    """ Chat request data structure. """
    messages: List[Message]
    userLocations: List[User]
