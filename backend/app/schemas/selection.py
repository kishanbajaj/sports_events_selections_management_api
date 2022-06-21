from enum import Enum
from typing import Optional
from pydantic import validator
from app.schemas.base import CommonBaseModel

class SelectionOutcomeModel(str, Enum):
    unsettled = "Unsettled"
    void = "Void"
    lose = "Lose"
    win = "Win"

class SelectionBaseModel(CommonBaseModel):
    event_id: int
    price: float
    outcome: SelectionOutcomeModel

    @validator('price')
    def truncate_float(cls, value: float) -> float: #pylint: disable=no-self-argument
        return float(round(value,2))


class SelectionCreateModel(SelectionBaseModel):
    pass

class SelectionUpdateModel(SelectionBaseModel):
    name: Optional[str]
    active: Optional[bool]
    event_id: Optional[int]
    price: Optional[float]
    outcome: Optional[SelectionOutcomeModel]

class SelectionPersistModel(SelectionBaseModel):
    id: int