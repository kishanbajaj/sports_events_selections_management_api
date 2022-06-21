from typing import List, Optional
from asyncpg import ForeignKeyViolationError
from fastapi import APIRouter, Depends, HTTPException

from app.api_routes.deps import get_repository
from app.db.repository.events import EventRepository
from app.schemas.event import EventCreateModel, EventPersistModel, EventUpdateModel

router = APIRouter()


@router.get("/{id}/", response_model=EventPersistModel, name="Get Event by id")
async def get_event_by_id(
    id: int, events_repo: EventRepository = Depends(get_repository(EventRepository))
) -> EventPersistModel:
    event = await events_repo.get_event_by_id(id=id)
    if not event:
        raise HTTPException(status_code=404, detail="Event ID not found.")
    return event

@router.get("/", response_model=List[EventPersistModel], name="Get all Events")
async def get_all_events(name: Optional[str] = None, active_selections_count: Optional[int] = None,
    events_repo: EventRepository = Depends(get_repository(EventRepository)),
) -> List[EventPersistModel]:
    search_filters = {"name": name,"active_selections_count": active_selections_count}
    return await events_repo.get_all_events(search_filters)


@router.post("/", response_model=EventPersistModel, name="Create Event")
async def create_event(
    new_event: EventCreateModel,
    event_repo: EventRepository = Depends(get_repository(EventRepository)),
) -> EventPersistModel:
    created_event = await event_repo.create_event(new_event=new_event)
    return created_event


@router.put("/{id}/", response_model=EventPersistModel, name="Update Event")
async def update_event(
    id: int, event_update: EventUpdateModel,
    events_repo: EventRepository = Depends(get_repository(EventRepository)),
) -> EventPersistModel:
    try:
        updated_event = await events_repo.update_event(id=id, event_update=event_update)
    except ForeignKeyViolationError:
        raise HTTPException(status_code=404, detail="Sport ID not found.")

    if not updated_event:
        raise HTTPException(status_code=404, detail="Event ID not found.")
    
    return updated_event