from typing import Callable, Type
from databases import Database
from fastapi import Depends
from starlette.requests import Request
from app.db.repository.base import BaseRepository


def get_db(request: Request) -> Database:
    return request.app.state._db


def get_repository(Repo_type: Type[BaseRepository]) -> Callable:
    def get_repo(db: Database = Depends(get_db)) -> Type[BaseRepository]:
        return Repo_type(db)

    return get_repo