""" Server for the place search API. """
import logging
import time
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routers.places import router as places_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Request/Response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """General logging middleware for the server.

    Args:
        request (Request): The request object.
        call_next: The next middleware function to call.

    Returns:
        The response object.
    """
    start_time = time.time()
    # Log request with more details
    logger.info("[LOG]: Request: %s (Path: %s, Query: %s, Body: %s)", 
                request.method, 
                request.url.path,
                str(request.query_params),
                str(request.body))

    # Get response
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Log response with more details
    logger.info("[LOG]: Response: %d - Processed in %.2fs (Path: %s, Body: %s)",
                response.status_code,
                process_time,
                request.url.path,
                str(response))

    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(places_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
