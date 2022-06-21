import json
import pytest
from fastapi import FastAPI

from typing import Any, List
from httpx import AsyncClient
from databases import Database
from datetime import datetime, timedelta, timezone

from tests.utils import generate_random_string

from app.db.repository.sports import SportRepository
from app.db.repository.events import EventRepository
from app.db.repository.selections import SelectionRepository

from app.schemas.sport import SportPersistModel
from app.schemas.event import EventCreateModel, EventPersistModel, EventStatusModel, EventTypeModel
from app.schemas.selection import SelectionCreateModel, SelectionOutcomeModel, SelectionUpdateModel


pytestmark = pytest.mark.asyncio


class TestEventRoutes:
    """Tests for the /events route."""

    @pytest.mark.asyncio
    async def test_route_exist(self, app: FastAPI, client: AsyncClient) -> None:
        """Test that the route exists."""
        res = await client.post(app.url_path_for("Create Event"), json={})
        assert res.status_code != 404

    @pytest.mark.asyncio
    async def test_invalid_input_raises_error(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        """Test if an invalid input raises error"""
        res = await client.post(app.url_path_for("Create Event"), json={})
        assert res.status_code == 422


class TestCreateEvent:
    """Test creating an Event."""

    async def test_creates_event_with_valid_input(
        self, app: FastAPI, client: AsyncClient, new_event: EventCreateModel
    ) -> None:
        """Test if a new event is successfully created with a valid input."""
        response = await client.post(
            app.url_path_for("Create Event"),
            json=json.loads(new_event.json()),
        )
        assert response.status_code == 200
        created_event = EventCreateModel(**response.json())
        assert created_event == new_event
        complete_created_event = EventPersistModel(**response.json())
        assert complete_created_event
        assert complete_created_event.id

    @pytest.mark.parametrize(
        "invalid_payload, status_code",
        (
            (None, 422),
            ({}, 422),
            ({"name": "test_name"}, 422),
            ({"slug": "my-slug"}, 422),
            ({"name": "test_name", "slug": "test"}, 422),
            ({"name": "test_name", "active": True}, 422),
            (
                {"name": "test_name", "active": True, "slug": "bad slug"},
                422,
            ),
            (
                {"name": "", "active": True, "slug": "nice-slug"},
                422,
            ),
            (
                {
                    "name": generate_random_string(101),
                    "active": True,
                    "slug": "nice-slug",
                },
                422,
            ),
            (
                {
                    "name": "nice name",
                    "active": True,
                    "slug": generate_random_string(151),
                },
                422,
            ),
            (
                {"name": "nice name", "active": True, "slug": ""},
                422,
            ),
            (
                {
                    "name": "nice name",
                    "active": True,
                    "slug": "ok",
                    "type": "nope",
                    "sport_id": "1",
                    "status": "pending",
                    "scheduled_start": "2022-04-09T21:21:22.830768",
                },
                422,
            ),
            (
                {
                    "name": "nice name",
                    "active": True,
                    "slug": "ok",
                    "type": "inplay",
                    "sport_id": "1",
                    "status": "dont exist",
                    "scheduled_start": "2022-04-09T21:21:22.830768",
                },
                422,
            ),
            (
                {
                    "name": "nice name",
                    "active": True,
                    "slug": "ok",
                    "type": "inplay",
                    "sport_id": "1",
                    "status": "pending",
                    "scheduled_start": "2022 04 21",
                },
                422,
            ),
        ),
    )
    async def test_invalid_input_raises_error(
        self,
        app: FastAPI,
        client: AsyncClient,
        invalid_payload: dict,
        status_code: int,
    ) -> None:
        """Test if error is returned when invalid input is provided."""
        response = await client.post(
            app.url_path_for("Create Event"),
            json=invalid_payload,
        )
        assert response.status_code == status_code

    async def test_creating_an_inactive_event_deactivates_an_active_sport_without_other_events(
        self,
        app: FastAPI,
        client: AsyncClient,
        new_sport_db_record: SportPersistModel,
        db: Database,
    ) -> None:
        """Test if when creating an inactive event under an active sport with no other events it will be deactivated."""
        # Making sure the Sport is active
        assert new_sport_db_record.active is True

        # Creating a new inactive event
        new_event = EventCreateModel(
            name=generate_random_string(50),
            active=False,
            slug=generate_random_string(20),
            type=EventTypeModel.preplay,
            sport_id=new_sport_db_record.id,
            status=EventStatusModel.started,
            scheduled_start=datetime.utcnow().replace(tzinfo=timezone.utc),
        )

        response = await client.post(
            app.url_path_for("Create Event"),
            json=json.loads(new_event.json()),
        )
        assert response.status_code == 200

        # Make sure that the sport is now inactive
        sport_repository = SportRepository(db)
        sport_is_active = await sport_repository.get_sport_by_id(id=new_sport_db_record.id)
        
        assert dict(sport_is_active)["active"] is False
    
    async def test_creating_an_inactive_event_under_sport_with_other_active_events_wont_have_effects(
        self,
        app: FastAPI,
        client: AsyncClient,
        new_event_db_record: EventPersistModel,
        db: Database,
    ) -> None:
        """Test if when creating an inactive event under an active sport with other active events it will do nothing."""
        # Making sure the Sport is active
        sport_repository = SportRepository(db)
        sport = await sport_repository.get_sport_by_id(id=new_event_db_record.sport_id)
        assert sport.active is True

        # Creating a new inactive event under the same sport
        new_event = EventCreateModel(
            name=generate_random_string(50),
            active=False,
            slug=generate_random_string(20),
            type=EventTypeModel.preplay,
            sport_id=sport.id,
            status=EventStatusModel.started,
            scheduled_start=datetime.utcnow().replace(tzinfo=timezone.utc),
        )

        response = await client.post(
            app.url_path_for("Create Event"),
            json=json.loads(new_event.json()),
        )
        assert response.status_code == 200

        # Make sure that the sport is still active
        sport_is_active = await sport_repository.get_sport_by_id(id=sport.id)
        assert dict(sport_is_active)["active"] is True

    async def test_creating_a_started_event_will_fill_actual_start_field(
        self,
        app: FastAPI,
        client: AsyncClient,
        new_sport_db_record: SportPersistModel,
        db: Database,
    ) -> None:
        """Test if creating an active event the actual start field is filled."""
        # Creating new event
        new_event = EventCreateModel(
            name=generate_random_string(30),
            active=True,
            slug=generate_random_string(24),
            type=EventTypeModel.inplay,
            sport_id=new_sport_db_record.id,
            status=EventStatusModel.started,
            scheduled_start=datetime.utcnow().replace(tzinfo=timezone.utc),
        )

        response = await client.post(
            app.url_path_for("Create Event"),
            json=json.loads(new_event.json()),
        )
        assert response.status_code == 200
        event = EventPersistModel(**response.json())
        assert event.actual_start
        assert event.actual_start < datetime.utcnow().replace(tzinfo=timezone.utc)


class TestGetEvent:
    """Test getting event."""

    async def test_get_event_by_id(
        self, app: FastAPI, client: AsyncClient, new_event_db_record: EventPersistModel
    ) -> None:
    
        """Test getting event by ID."""
        response = await client.get(
            app.url_path_for("Get Event by id", id=new_event_db_record.id)
        )
        assert response.status_code == 200
    
    @pytest.mark.parametrize(
        "invalid_id, status_code",
        (
            (None, 422),
            (-1, 404),
        ),
    )
    async def test_get_event_by_id_with_nonexistent_id(
        self, app: FastAPI, client: AsyncClient, invalid_id: int, status_code: int
    ) -> None:
        """Test getting an event with nonexistent id returns 404."""
        response = await client.get(app.url_path_for("Get Event by id", id=invalid_id))

        assert response.status_code == status_code

    async def test_get_all_events(
        self, app: FastAPI, client: AsyncClient, new_event_db_record: EventPersistModel
    ) -> None:
        """Test getting all events."""
        response = await client.get(app.url_path_for("Get all Events"))

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0


    async def test_get_all_events_with_name_regex_filter(
        self, app: FastAPI, client: AsyncClient, new_sport_db_record: SportPersistModel
    ) -> None:
        """Test getting events that satisfies filters."""
        # RegEx filter
        champions_league = "Cham.*gue.*"

        # Creating first event
        response = await client.post(
            app.url_path_for("Create Event"),
            json=json.loads(
                EventCreateModel(
                    name="Champions League 2020-2021",
                    slug="champions-league-2020-2021",
                    active=False,
                    type=EventTypeModel.preplay.value,
                    sport_id=new_sport_db_record.id,
                    status=EventStatusModel.ended.value,
                    scheduled_start=datetime.utcnow().replace(tzinfo=timezone.utc),
                ).json()
            ),
        )
        assert response.status_code == 200
        first_event = EventPersistModel(**response.json())

        response = await client.get(
            app.url_path_for("Get all Events"),
            params={"name": champions_league},
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        event = EventPersistModel(**response.json()[0])
        assert event == first_event

        # Creating second event
        response = await client.post(
            app.url_path_for("Create Event"),
            json=json.loads(
                EventCreateModel(
                    name="Champions League 2021-2022",
                    slug="champions-league-2021-2022",
                    active=True,
                    type=EventTypeModel.preplay.value,
                    sport_id=new_sport_db_record.id,
                    status=EventStatusModel.started.value,
                    scheduled_start=datetime.utcnow().replace(tzinfo=timezone.utc),
                ).json()
            ),
        )
        assert response.status_code == 200
        second_event = EventPersistModel(**response.json())

        response = await client.get(
            app.url_path_for("Get all Events"),
            params={"name": champions_league},
        )
        assert response.status_code == 200
        assert len(response.json()) > 0
        all_events = [EventPersistModel(**event) for event in response.json()]
        assert first_event in all_events
        assert second_event in all_events

    async def test_get_all_events_by_minimum_active_selections(
        self,
        app: FastAPI,
        client: AsyncClient,
        new_event_db_record: EventPersistModel,
        db: Database,
    ) -> None:
        """Test getting events by using single filters."""
        response = await client.get(
            app.url_path_for("Get all Events"),
            params={"active_selections_count": 0, "name": new_event_db_record.name},
        )
        assert response.status_code == 200
        assert len(response.json()) == 0

        # Creating an INACTIVE Selection under the Sport
        new_selection = SelectionCreateModel(
            name="My Selection",
            active=False,
            event_id=new_event_db_record.id,
            price=599.99,
            outcome=SelectionOutcomeModel.lose,
        )
        selection_repository = SelectionRepository(db)
        selection = await selection_repository.create_selection(
            new_selection=new_selection
        )

        # We should get the same result
        response = await client.get(
            app.url_path_for("Get all Events"),
            params={"active_selections_count": 0, "name": new_event_db_record.name},
        )
        assert response.status_code == 200
        assert len(response.json()) == 0

        # Update the selection to active state
        selection_update = SelectionUpdateModel(active=True)
        await selection_repository.update_selection(
            id=selection.id, selection_update=selection_update
        )

        # We should get the event back
        response = await client.get(
            app.url_path_for("Get all Events"),
            params={"active_selections_count": 0, "name": new_event_db_record.name},
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
    

class TestUpdateEvent:
    """Test updating an Event."""

    @pytest.mark.parametrize(
        "attributes_to_update, values",
        (
            (["name"], ["My new name"]),
            (["slug"], ["a-nicely-formatted-slug"]),
            (["active"], [False]),
            (["type"], [EventTypeModel.preplay.value]),
            (["sport_id"], [1]),
            (["status"], [EventStatusModel.ended.value]),
            (
                [
                    "name",
                    "slug",
                    "active",
                    "type",
                    "sport_id",
                    "status",
                ],
                [
                    "Another beautiful name",
                    "some-slug",
                    False,
                    EventTypeModel.preplay.value,
                    1,
                    EventStatusModel.pending.value,
                ],
            ),
        ),
    )
    async def test_updates_event_with_valid_input(
        self,
        app: FastAPI,
        client: AsyncClient,
        new_event_db_record: EventPersistModel,
        attributes_to_update: List[str],
        values: List[Any],
    ) -> None:
        """Test if an existing event is successfully updated with a valid input."""
        values_to_update = {
            attributes_to_update[i]: values[i] for i in range(len(attributes_to_update))
        }

        response = await client.put(
            app.url_path_for("Update Event", id=new_event_db_record.id),
            json=values_to_update,
        )

        assert response.status_code == 200
        updated_event = EventPersistModel(**response.json())
        assert updated_event.id == new_event_db_record.id
        # 1. Asserting that every field that should be updated is updated
        for i, attr_to_update in enumerate(attributes_to_update):
            attribute = getattr(updated_event, attr_to_update)
            assert attribute == values[i]
            assert attribute != getattr(new_event_db_record, attr_to_update)
        # 2. Asserting that every field that should NOT be updated remains the same
        for attr, value in updated_event.dict().items():
            if attr not in attributes_to_update:
                assert getattr(new_event_db_record, attr) == value

    @pytest.mark.parametrize(
        "attributes_to_update, values",
        (
            (
                ["scheduled_start"],
                [
                    str(
                        datetime.utcnow().replace(tzinfo=timezone.utc)
                        - timedelta(days=10)
                    )
                ],
            ),
            (["actual_start"], [str(datetime.utcnow().replace(tzinfo=timezone.utc))]),
        ),
    )
    async def test_updates_event_with_valid_input_timestamps(
        self,
        app: FastAPI,
        client: AsyncClient,
        new_event_db_record: EventPersistModel,
        attributes_to_update: List[str],
        values: List[Any],
    ) -> None:
        """Test if an existing event is successfully updated with a valid input."""
        values_to_update = {
            attributes_to_update[i]: values[i] for i in range(len(attributes_to_update))
        }

        response = await client.put(
            app.url_path_for("Update Event", id=new_event_db_record.id),
            json=values_to_update,
        )

        assert response.status_code == 200
        updated_event = EventPersistModel(**response.json())
        assert updated_event.id == new_event_db_record.id
        # 1. Asserting that every field that should be updated is updated
        for i, attr_to_update in enumerate(attributes_to_update):
            attribute = getattr(updated_event, attr_to_update)
            assert str(attribute) == values[i]
            assert attribute != getattr(new_event_db_record, attr_to_update)
        # 2. Asserting that every field that should NOT be updated remains the same
        for attr, value in updated_event.dict().items():
            if attr not in attributes_to_update:
                assert getattr(new_event_db_record, attr) == value

    @pytest.mark.parametrize(
        "id, event_update, status_code",
        (
            (1, {"type": "invalid enum"}, 422),
            (1, {"status": "invalid enum"}, 422),
            (1, {"scheduled_start": "2020 a"}, 422),
            (1, {"actual_start": "2021-"}, 422),
            (1, {"sport_id": -1}, 404),
            (-1, {"name": "A nice name"}, 404),
        ),
    )
    async def test_updates_event_fails_with_invalid_input(
        self,
        app: FastAPI,
        client: AsyncClient,
        new_event_db_record: EventPersistModel,
        id: int,
        event_update: dict,
        status_code: int,
    ) -> None:
        """Test that the update fails if a bad input is given."""
        id = id if id < 0 else new_event_db_record.id

        response = await client.put(
            app.url_path_for("Update Event", id=id),
            json=event_update,
        )
        assert response.status_code == status_code

    async def test_sport_inactive_when_the_only_active_event_is_updated_to_inactive(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Database,
        new_event_db_record: EventPersistModel,
    ) -> None:
        """Test if the sport will be inactivated when the only active event becomes inactive."""
        # Creating one more event under the same sport
        event_repository = EventRepository(db)
        event_create = EventCreateModel(**new_event_db_record)
        event_create.name = "new name"
        second_event = await event_repository.create_event(new_event=event_create)
        assert second_event

        # Checking that the sport is active
        sport_repository = SportRepository(db)
        sport: SportPersistModel = await sport_repository.get_sport_by_id(
            id=new_event_db_record.sport_id
        )
        assert sport.active is True

        # Deactivating the first event
        response = await client.put(
            app.url_path_for("Update Event", id=new_event_db_record.id),
            json={"active": False},
        )
        assert response.status_code == 200
        sport: SportPersistModel = await sport_repository.get_sport_by_id(
            id=new_event_db_record.sport_id
        )
        assert sport.active is True

        # Deactivating the second event
        response = await client.put(
            app.url_path_for("Update Event", id=second_event.id),
            json={"active": False},
        )
        # Now the sport should be inactive
        sport: SportPersistModel = await sport_repository.get_sport_by_id(
            id=new_event_db_record.sport_id
        )
        assert sport.active is False


    async def test_updating_event_with_started_status_will_fill_actual_start(
        self,
        app: FastAPI,
        client: AsyncClient,
        new_event_db_record: EventPersistModel,
    ) -> None:
        """Test if updating an event with started as status will fill the actual_start field."""
        assert new_event_db_record.actual_start is None

        response = await client.put(
            app.url_path_for("Update Event", id=new_event_db_record.id),
            json={"status": EventStatusModel.started.value},
        )
        assert response.status_code == 200
        event = EventPersistModel(**response.json())
        assert event.actual_start
        assert event.actual_start < datetime.utcnow().replace(tzinfo=timezone.utc)

        old_actual_start = event.actual_start

        # Making sure that we can update the record with the actual_start
        # and the status
        response = await client.put(
            app.url_path_for("Update Event", id=new_event_db_record.id),
            json={
                "actual_start": str(
                    datetime.utcnow().replace(tzinfo=timezone.utc)
                    + timedelta(minutes=1)
                )
            },
        )
        assert response.status_code == 200
        event = EventPersistModel(**response.json())
        assert event.actual_start
        assert event.actual_start > old_actual_start