from typing import Optional
from app.schemas.base import CommonBaseModel


class SportBaseModel(CommonBaseModel):
    slug: str

class SportCreateModel(SportBaseModel):
    pass

class SportUpdateModel(SportBaseModel):
    name: Optional[str]
    slug: Optional[str]
    active: Optional[bool]
    
class SportPersistModel(SportBaseModel):
    id: int