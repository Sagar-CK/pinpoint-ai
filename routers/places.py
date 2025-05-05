"""Router for the places API."""

import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import requests
from google import genai
from google.genai import types

from utils.constants import MAPS_API_URL, GOOGLE_API_KEY, LITE_MODEL, PRO_MODEL
from utils.prompts import CREATE_QUERY_PROMPT, JUSTIFICATION_PROMPT
from models.place import (
    PlaceFullResponse,
    SearchRequest,
    Location,
    SearchResponse,
    Availability,
)
from models.chat import ChatRequest

router = APIRouter(prefix="/places")

client = genai.Client(api_key=GOOGLE_API_KEY)


@router.post("/chat", response_model=SearchResponse)
async def find_places(request: ChatRequest) -> StreamingResponse:
    """Get the request body for the maps API.

    Args:
        request (ChatRequest): The chat request.

    Returns:
        A streaming response containing places and justification.
    """
    messages = request.messages
    formatted_messages = [
        types.Content(
            role=message.role, parts=[types.Part.from_text(text=message.content)]
        )
        for message in messages
    ]

    response = client.models.generate_content(
        model=LITE_MODEL,
        contents=formatted_messages,
        config=types.GenerateContentConfig(
            system_instruction=CREATE_QUERY_PROMPT.format(
                conversation_history="\n".join(
                    [message.content for message in messages]
                )
            )
        ),
    )

    async def generate_response():
        response_builder = {}
        # First get and stream the places
        places = await get_places_from_maps(
            SearchRequest(query=response.text, messages=messages)
        )
        response_builder["places"] = [place.model_dump() for place in places.places]
        response_builder["justification"] = ""
        yield f"event: places\ndata: {json.dumps(response_builder)}\n\n"

        # Then stream the justification
        async for chunk in await client.aio.models.generate_content_stream(
            model=LITE_MODEL,
            contents=JUSTIFICATION_PROMPT.format(
                conversation_history="\n".join(
                    [message.content for message in messages]
                ),
                search_query=response.text,
                places=places.places,
            ),
        ):
            response_builder["justification"] += chunk.text
            yield f"event: response\ndata: {json.dumps(response_builder)}\n\n"

    return StreamingResponse(generate_response(), media_type="text/event-stream")


async def get_places_from_maps(request: SearchRequest) -> SearchResponse:
    """Get places from the maps API.

    Returns:
        The places from the maps API.
    """
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.websiteUri,places.googleMapsUri,places.types,places.currentOpeningHours,places.accessibilityOptions,places.businessStatus,places.goodForChildren,places.goodForGroups,places.liveMusic,places.allowsDogs,places.outdoorSeating,places.parkingOptions,places.dineIn,places.delivery,places.internationalPhoneNumber,places.photos,places.rating,places.userRatingCount,places.reservable,places.priceRange,places.priceLevel,places.location",
    }

    body = {"textQuery": request.query}

    print(body)

    response = requests.post(MAPS_API_URL, headers=headers, json=body, timeout=1000)

    data = response.json()

    print(data)

    if "places" not in data or not data["places"]:
        return SearchResponse(
            places=[], justification="No places found matching your query."
        )

    def map_to_availability(value):
        if value is True or value == "TRUE" or value == "true":
            return Availability.TRUE
        elif value is False or value == "FALSE" or value == "false":
            return Availability.FALSE
        else:
            return Availability.NOT_AVAILABLE

    places = [
        PlaceFullResponse(
            id=place["id"],
            displayName=place["displayName"]["text"],
            formattedAddress=place["formattedAddress"],
            rating=place["rating"],
            googleMapsUri=place["googleMapsUri"],
            websiteUri=place["websiteUri"] if "websiteUri" in place else None,
            location=Location(
                latitude=place["location"]["latitude"],
                longitude=place["location"]["longitude"],
            ),
            userRatingCount=place["userRatingCount"],
            types=place["types"],
            currentOpeningHours=(
                place["currentOpeningHours"]["weekdayDescriptions"]
                if "currentOpeningHours" in place
                else None
            ),
            goodForChildren=(
                map_to_availability(place["goodForChildren"])
                if "goodForChildren" in place
                else Availability.NOT_AVAILABLE
            ),
            goodForGroups=(
                map_to_availability(place["goodForGroups"])
                if "goodForGroups" in place
                else Availability.NOT_AVAILABLE
            ),
            liveMusic=(
                map_to_availability(place["liveMusic"])
                if "liveMusic" in place
                else Availability.NOT_AVAILABLE
            ),
            allowedDogs=(
                map_to_availability(place["allowedDogs"])
                if "allowedDogs" in place
                else Availability.NOT_AVAILABLE
            ),
            outdoorSeating=(
                map_to_availability(place["outdoorSeating"])
                if "outdoorSeating" in place
                else Availability.NOT_AVAILABLE
            ),
            parkingOptions=(
                map_to_availability(place["parkingOptions"])
                if "parkingOptions" in place
                else Availability.NOT_AVAILABLE
            ),
            dineIn=(
                map_to_availability(place["dineIn"])
                if "dineIn" in place
                else Availability.NOT_AVAILABLE
            ),
            delivery=(
                map_to_availability(place["delivery"])
                if "delivery" in place
                else Availability.NOT_AVAILABLE
            ),
            reservable=(
                map_to_availability(place["reservable"])
                if "reservable" in place
                else Availability.NOT_AVAILABLE
            ),
            priceLevel=place["priceLevel"] if "priceLevel" in place else None,
            priceRange=place["priceRange"] if "priceRange" in place else None,
            photos=(
                [photo["googleMapsUri"] for photo in place["photos"]]
                if "photos" in place
                else None
            ),
            internationalPhoneNumber=(
                place["internationalPhoneNumber"]
                if "internationalPhoneNumber" in place
                else None
            ),
            businessStatus=(
                place["businessStatus"] if "businessStatus" in place else None
            ),
        )
        for place in data["places"]
    ]

    return SearchResponse(places=places, justification="")
