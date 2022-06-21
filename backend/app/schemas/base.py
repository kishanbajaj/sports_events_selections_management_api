from pydantic import BaseModel

class CommonBaseModel(BaseModel):
    name: str
    active: bool