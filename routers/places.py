"""Router for the places API."""

import json
import asyncio
from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import requests
from google import genai
from google.genai import types

from utils.constants import MAPS_API_URL, GOOGLE_API_KEY, LITE_MODEL
from utils.prompts import (
    CREATE_QUERY_PROMPT,
    JUSTIFICATION_PROMPT,
    SCORING_PROMPT,
    FINAL_SCORING_PROMPT,
)
from models.place import (
    PlaceFullResponse,
    Place,
    PlaceRanking,
    SearchRequest,
    Location,
    SearchResponse,
    Availability,
    UserPreferences,
    PriceRange,
)
from models.chat import ChatRequest, Message

router = APIRouter(prefix="/places")

client = genai.Client(api_key=GOOGLE_API_KEY)


def map_to_availability(value):
    """Map a value to an availability enum.

    Args:
        value: The value to map.

    Returns:
        The mapped availability.
    """
    if value is True or value == "TRUE" or value == "true":
        return Availability.TRUE
    elif value is False or value == "FALSE" or value == "false":
        return Availability.FALSE
    else:
        return Availability.NOT_AVAILABLE


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
        response_builder["user_preferences"] = [
            user_preference.model_dump()
            for user_preference in places.user_preferences
        ]
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
                final_scores=places.user_preferences,
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

    response = requests.post(MAPS_API_URL, headers=headers, json=body, timeout=1000)

    data = response.json()

    if "places" not in data or not data["places"]:
        return SearchResponse(
            places=[], justification="No places found matching your query."
        )
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
            priceRange=PriceRange(
                startPrice=place["priceRange"]["startPrice"]["currencyCode"] + " " + place["priceRange"]["startPrice"]["units"] if "priceRange" in place and "startPrice" in place["priceRange"] else None,
                endPrice=place["priceRange"]["endPrice"]["currencyCode"] + " " + place["priceRange"]["endPrice"]["units"] if "priceRange" in place and "endPrice" in place["priceRange"] else None,
            ),
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

    user_preferences = await get_user_preferences(request.messages, places)

    return SearchResponse(
        places=places, justification="", user_preferences=user_preferences
    )


async def get_user_preferences(
    messages: List[Message], places: List[PlaceFullResponse]
) -> List[UserPreferences]:
    """Get the user preferences for the places.

    Returns:
        The user preferences for the places.
    """

    async def get_place_score(place_full_response: PlaceFullResponse) -> PlaceRanking:
        place_details = Place(
            id=place_full_response.id,
            displayName=place_full_response.displayName,
            location=place_full_response.location,
            rating=place_full_response.rating,
            userRatingCount=place_full_response.userRatingCount,
            types=place_full_response.types,
            currentOpeningHours=place_full_response.currentOpeningHours,
            goodForChildren=place_full_response.goodForChildren,
            goodForGroups=place_full_response.goodForGroups,
            liveMusic=place_full_response.liveMusic,
            allowedDogs=place_full_response.allowedDogs,
            outdoorSeating=place_full_response.outdoorSeating,
            parkingOptions=place_full_response.parkingOptions,
            dineIn=place_full_response.dineIn,
            delivery=place_full_response.delivery,
            reservable=place_full_response.reservable,
            priceLevel=place_full_response.priceLevel,
            priceRange=place_full_response.priceRange,
        )

        place_score_pv = await client.aio.models.generate_content(
            model=LITE_MODEL,
            contents=SCORING_PROMPT.format(
                conversation_history="\n".join(
                    [message.content for message in messages]
                ),
                place_details=place_details,
            ),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PlaceRanking,
            ),
        )

        if not place_score_pv.parsed:
            raise HTTPException(status_code=500, detail="Failed to parse place ranking")

        place_score = place_score_pv.parsed
        place_score.id = place_full_response.id
        return place_score

    # Get all place scores in parallel
    place_scores = await asyncio.gather(
        *[get_place_score(place) for place in places]
    )

    async def get_final_score(place_score: PlaceRanking) -> UserPreferences:
        final_score_pv = await client.aio.models.generate_content(
            model=LITE_MODEL,
            contents=FINAL_SCORING_PROMPT.format(
                conversation_history="\n".join(
                    [message.content for message in messages]
                ),
                place_scores=place_scores,
            ),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=UserPreferences,
            ),
        )

        if not final_score_pv.parsed:
            raise HTTPException(status_code=500, detail="Failed to parse final score")

        final_score = final_score_pv.parsed
        final_score.place_id = place_score.id
        return final_score

    # Get all final scores in parallel
    user_preferences = await asyncio.gather(
        *[get_final_score(place_score) for place_score in place_scores]
    )

    return user_preferences
