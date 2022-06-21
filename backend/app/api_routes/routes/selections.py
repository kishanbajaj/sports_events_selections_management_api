from typing import List, Optional
from asyncpg import ForeignKeyViolationError
from fastapi import APIRouter, Depends, HTTPException

from app.api_routes.deps import get_repository
from app.db.repository.selections import SelectionRepository
from app.schemas.selection import SelectionCreateModel, SelectionPersistModel, SelectionUpdateModel

router = APIRouter()

@router.get("/{id}/", response_model=SelectionPersistModel, name="Get Selection by id")
async def get_selection_by_id(
    id: int, selections_repo: SelectionRepository = Depends(get_repository(SelectionRepository)),
) -> SelectionPersistModel:
    selection = await selections_repo.get_selection_by_id(id=id)
    if not selection:
        raise HTTPException(status_code=404, detail="Selection ID not found.")
    return selection


@router.get("/", response_model=List[SelectionPersistModel], name="Get all Selections")
async def get_all_selections(
    name: Optional[str] = None,
    selections_repo: SelectionRepository = Depends(get_repository(SelectionRepository)),
) -> List[SelectionPersistModel]:
    search_filters = {"name": name}
    return await selections_repo.get_all_selections(search_filters)


@router.post("/", response_model=SelectionPersistModel, name="Create Selection")
async def create_selection(
    new_selection: SelectionCreateModel,
    selection_repo: SelectionRepository = Depends(get_repository(SelectionRepository)),
) -> SelectionPersistModel:
    created_selection = await selection_repo.create_selection(new_selection=new_selection)
    return created_selection


@router.put("/{id}/", response_model=SelectionPersistModel, name="Update Selection")
async def update_selection(
    id: int, selection_update: SelectionUpdateModel,
    selections_repo: SelectionRepository = Depends(get_repository(SelectionRepository)),
) -> SelectionPersistModel:
    try:
        updated_selection = await selections_repo.update_selection(id=id, selection_update=selection_update)
    except ForeignKeyViolationError:
        raise HTTPException(status_code=404, detail="Event ID not found.")

    if not updated_selection:
        raise HTTPException(
            status_code=404, detail="Selection ID not found.")
            
    return updated_selection
