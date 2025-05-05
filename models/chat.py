""" Chat request data structures. """
from typing import List
from pydantic import BaseModel

class Message(BaseModel):
    """ Message data structure. """
    role: str
    content: str

class ChatRequest(BaseModel):
    """ Chat request data structure. """
    messages: List[Message]
