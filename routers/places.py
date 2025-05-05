"""Router for the places API."""

import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import requests
from google import genai
from google.genai import types

from utils.constants import MAPS_API_URL, GOOGLE_API_KEY, LITE_MODEL, PRO_MODEL
from utils.prompts import CREATE_QUERY_PROMPT, JUSTIFICATION_PROMPT
from models.place import Place, SearchRequest, Location, SearchResponse
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
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.googleMapsUri,places.websiteUri,places.location",
    }

    body = {"textQuery": request.query}

    response = requests.post(MAPS_API_URL, headers=headers, json=body, timeout=1000)

    data = response.json()

    if "places" not in data or not data["places"]:
        return SearchResponse(
            places=[], justification="No places found matching your query."
        )

    places = [
        Place(
            displayName=place["displayName"]["text"],
            formattedAddress=place["formattedAddress"],
            rating=place["rating"],
            googleMapsUri=place["googleMapsUri"],
            websiteUri=place["websiteUri"] if "websiteUri" in place else None,
            location=Location(
                latitude=place["location"]["latitude"],
                longitude=place["location"]["longitude"],
            ),
        )
        for place in data["places"]
    ]

    return SearchResponse(places=places, justification="")
