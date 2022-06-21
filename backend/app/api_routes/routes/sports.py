from databases import Database
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException

from app.api_routes.deps import get_repository
from app.db.repository.sports import SportRepository
from app.schemas.sport import SportCreateModel, SportPersistModel, SportUpdateModel

router = APIRouter()

@router.get("/{id}/", response_model = SportPersistModel,name="Get Sport by id")
async def get_sport_by_id(
    id: int,
    sports_repo: SportRepository = Depends(get_repository(SportRepository))
) -> SportPersistModel:

    sport = await sports_repo.get_sport_by_id(id=id)

    if not sport:
        raise HTTPException(status_code=404, detail="Sport ID not found.")

    return sport


@router.get("/", response_model=List[SportPersistModel],name="Get all Sports")
async def get_all_sports(
    name: Optional[str] = None,
    active_events_count: Optional[int] = None,
    sports_repo: SportRepository = Depends(get_repository(SportRepository)),
) -> List[SportPersistModel]:

    search_filters = {"name": name, "active_events_count": active_events_count}

    return await sports_repo.get_all_sports(search_filters)


@router.post("/", response_model = SportPersistModel,name="Create Sport")
async def create_sport(
    new_sport: SportCreateModel,
    sports_repo: SportRepository = Depends(get_repository(SportRepository)),
) -> SportPersistModel:

    created_sport = await sports_repo.create_sport(new_sport=new_sport)

    return created_sport


@router.put("/{id}/", response_model = SportPersistModel,name="Update Sport")
async def update_sport(
    id: int,
    sport_update: SportUpdateModel,
    sports_repo: SportRepository = Depends(get_repository(SportRepository)),
) -> SportPersistModel:

    updated_sport = await sports_repo.update_sport(id=id, sport_update=sport_update)

    if not updated_sport:
        raise HTTPException(status_code=404, detail="Sport ID not found.")

    return updated_sport