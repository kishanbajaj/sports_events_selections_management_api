import os
import warnings
from datetime import datetime, timezone

import alembic
import pytest_asyncio
from alembic.config import Config
from databases import Database
from fastapi import FastAPI
from app.db.repository.selections import SelectionRepository
from app.schemas.selection import SelectionCreateModel, SelectionPersistModel, SelectionOutcomeModel
from app.db.repository.events import EventRepository
from app.db.repository.sports import SportRepository
from app.schemas.event import EventCreateModel, EventPersistModel, EventStatusModel, EventTypeModel
from app.schemas.sport import SportCreateModel, SportPersistModel
from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from app.config.app_config import appConfig

from tests.utils import generate_random_string

DATABASE_URI: str = "postgresql://postgres:kishan@localhost:5432/SB"

@pytest_asyncio.fixture(scope="session")
def apply_migrations():
    """Apply migrations when running tests, drop DB when finished."""
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    os.environ["TESTING"] = "1"
    config = Config("alembic.ini")
    alembic.command.upgrade(config, "head")
    yield
    alembic.command.downgrade(config, "base")

@pytest_asyncio.fixture
def app(apply_migrations: None) -> FastAPI:
    """Start the application."""
    from app.main import application
    return application()

@pytest_asyncio.fixture
async def db(app: FastAPI) -> Database:
    """Return a reference to the DB."""
    '''
    database = Database(
        DATABASE_URI,
        min_size=appConfig.DB_MIN_CONNECTION_POOL,
        max_size=appConfig.DB_MAX_CONNECTION_POOL,
    )
    await database.connect()
    app.state._db = database
    '''
    return app.state._db

@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncClient:
    """Make requests for tests."""
    async with LifespanManager(app):
        async with AsyncClient(
            app=app,
            base_url="http://testserver",
            headers={"Content-Type": "application/json"},
        ) as client:
            yield client

@pytest_asyncio.fixture
def new_sport() -> SportCreateModel:
    """Return sport fixture."""
    return SportCreateModel(name="my lovely sport", active=True, slug="my-lovely-sport")


@pytest_asyncio.fixture
async def new_sport_db_record(db: Database) -> SportPersistModel:
    sports_repo = SportRepository(db)
    new_sport = SportCreateModel(
        name=generate_random_string(length=10),
        active=True,
        slug=generate_random_string(10),
    )
    return await sports_repo.create_sport(new_sport=new_sport)

@pytest_asyncio.fixture
def new_event(new_sport_db_record: SportPersistModel) -> EventCreateModel:
    """Return event fixture."""
    return EventCreateModel(
        name=generate_random_string(50),
        active=True,
        slug="my-lovely-event",
        type=EventTypeModel.inplay,
        sport_id=new_sport_db_record.id,
        status=EventStatusModel.pending,
        scheduled_start=datetime.utcnow().replace(tzinfo=timezone.utc),
    )


@pytest_asyncio.fixture
async def new_event_db_record(
    db: Database, new_sport_db_record: SportPersistModel
) -> EventPersistModel:
    """Return event DB record."""
    events_repo = EventRepository(db)
    new_event = EventCreateModel(
        name=generate_random_string(50),
        active=True,
        slug=generate_random_string(50),
        type=EventTypeModel.inplay,
        sport_id=new_sport_db_record.id,
        status=EventStatusModel.cancelled,
        scheduled_start=datetime.utcnow().replace(tzinfo=timezone.utc),
    )
    return await events_repo.create_event(new_event=new_event)


@pytest_asyncio.fixture
def new_selection(new_event_db_record: EventPersistModel) -> SelectionCreateModel:
    """Return selection fixture."""
    return SelectionCreateModel(
        name=generate_random_string(50),
        active=True,
        event_id=new_event_db_record.id,
        price=9.99,
        outcome=SelectionOutcomeModel.unsettled,
    )


@pytest_asyncio.fixture
async def new_selection_db_record(
    db: Database, new_event_db_record: EventPersistModel
) -> SelectionPersistModel:
    """Return selection DB record."""
    selection_repo = SelectionRepository(db)
    new_selection = SelectionCreateModel(
        name=generate_random_string(50),
        active=True,
        event_id=new_event_db_record.id,
        price=9.99,
        outcome=SelectionOutcomeModel.unsettled,
    )
    return await selection_repo.create_selection(new_selection=new_selection)