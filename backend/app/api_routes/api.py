from fastapi import APIRouter

from app.api_routes.routes import sports, events, selections

api_router = APIRouter()
api_router.include_router(sports.router, prefix="/sports", tags=["sports"])
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(selections.router, prefix="/selections", tags=["selections"])