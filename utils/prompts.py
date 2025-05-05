"""Prompts for pin-point AI"""

CREATE_QUERY_PROMPT = """
Based on the conversation history of multiple users, create a search query to find preferred activities for them.

Conversation History:
{conversation_history}

Here are some examples, with explanations as to how they were created:
"10 High Street, UK" or "123 Main Street, US" 	Multiple "High Street"s in the UK; multiple "Main Street"s in the US. Query doesn't return desirable results unless a location restriction is set.
"ChainRestaurant New York" 	Multiple "ChainRestaurant" locations in New York; no street address or even street name.
"10 High Street, Escher UK" or "123 Main Street, Pleasanton US" 	Only one "High Street" in the UK city of Escher; only one "Main Street" in the US city of Pleasanton CA.
"UniqueRestaurantName New York" 	Only one establishment with this name in New York; no street address needed to differentiate.
"pizza restaurants in New York" 	This query contains its location restriction, and "pizza restaurants" is a well-defined place type. It returns multiple results.
"+1 514-670-8700" 	This query contains a phone number. It returns multiple results for places associated with that phone number.


In your response, ONLY RESPOND WITH THE QUERY, NOTHING ELSE.
"""

JUSTIFICATION_PROMPT = """
Based on the conversation history of multiple users, the created search query, and the list of places returned, and their final scores, create a justification for the results in a casual narrative format.
The justification should be based on the RESULTS not the search query or the final scores (don't mention the scores in the justification).

Conversation History:
{conversation_history}

Search Query:
{search_query}

Places:
{places}

Final Scores:
{final_scores}

Here is an example of the format you should follow:
I recommended Joe's Pizza because you guys mentioned you wanted something cheap and close to the hotel. I also included Thai Food 2 because Dan mentioned he likes thai food. ...

In your response, ONLY RESPOND WITH THE JUSTIFICATION, NOTHING ELSE.
"""

SCORING_PROMPT = """
Based on the conversation history and the place's details, return the place's score for each of the criteria (0-1) float. If there is a criteria that is not directly EXPLICITLY inferred from the conversation history, return -1 for that criteria.

Conversation History:
{conversation_history}

Place Details:
{place_details} 
"""

FINAL_SCORING_PROMPT = """
Based on the conversation history and the place's scores, return the final score for the place.

Conversation History:
{conversation_history}

Place Scores:
{place_scores}
"""
