"""Router for the places API."""

import os
from pprint import pprint
from typing import List
import requests

from fastapi import APIRouter

from utils.constants import MAPS_API_URL
from models.place import Place, SearchRequest

from dotenv import load_dotenv

load_dotenv()


router = APIRouter(prefix="/places")

@router.get("/query")
async def get_places_from_maps(request: SearchRequest) -> List[Place]:
    """Get places from the maps API.

    Returns:
        The places from the maps API.
    """
    
    print(os.getenv("GOOGLE_API_KEY"))
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Goog-Api-Key": os.getenv("GOOGLE_API_KEY"),
        "X-Goog-FieldMask": "displayName,formattedAddress,rating,googleMapsUri,websiteUri,location"
    }

    body = {
        "textQuery": request.query
    }

    response = requests.post(MAPS_API_URL, headers=headers, json=body, timeout=1000)

    data = response.json()

    pprint(data)

    return data["results"]