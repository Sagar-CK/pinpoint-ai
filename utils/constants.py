""" Constants for the server. """
import os
from dotenv import load_dotenv

load_dotenv(override=True)

MAPS_API_URL="https://places.googleapis.com/v1/places:searchText"
GOOGLE_API_KEY=os.getenv("GOOGLE_API_KEY")
LITE_MODEL="gemini-2.5-flash-preview-04-17"
PRO_MODEL="gemini-2.5-pro-preview-03-25"
