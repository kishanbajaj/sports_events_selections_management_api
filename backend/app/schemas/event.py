from enum import Enum
from typing import Optional
from datetime import datetime
from app.schemas.base import CommonBaseModel

class EventTypeModel(str, Enum):
    preplay = "preplay"
    inplay = "inplay"


class EventStatusModel(str, Enum):
    pending = "Pending"
    started = "Started"
    ended = "Ended"
    cancelled = "Cancelled"


class EventBaseModel(CommonBaseModel):
    slug: str
    type: EventTypeModel
    sport_id: int
    status: EventStatusModel
    scheduled_start: datetime
    actual_start: Optional[datetime]


class EventCreateModel(EventBaseModel):
    pass


class EventUpdateModel(EventBaseModel):
    name: Optional[str]
    active: Optional[bool]
    slug: Optional[str]
    type: Optional[EventTypeModel]
    sport_id: Optional[int]
    status: Optional[EventStatusModel]
    scheduled_start: Optional[datetime]
    actual_start: Optional[datetime]


class EventPersistModel(EventBaseModel):
    id: int