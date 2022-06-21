from datetime import datetime
from typing import Any, List
from databases import Database

import pytest
from app.db.repository.events import EventRepository
from app.schemas.event import (
    EventCreateModel,
    EventStatusModel,
    EventTypeModel,
)
from app.schemas.sport import SportCreateModel, SportPersistModel
from fastapi import FastAPI
from httpx import AsyncClient
from app.main import application
from tests.utils import generate_random_string

pytestmark = pytest.mark.asyncio


class TestSportsRoutes:
    """Tests for the /sports route."""
    @pytest.mark.asyncio
    async def test_route_exist(self, app: FastAPI, client: AsyncClient) -> None:
        """Test that the route exists."""
        res = await client.post(app.url_path_for("Create Sport"), json={})
        assert res.status_code != 404

    @pytest.mark.asyncio
    async def test_invalid_input_raises_error(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        """Test if an invalid input raises error"""
        res = await client.post(app.url_path_for("Create Sport"), json={})
        assert res.status_code == 422


class TestCreateSport:
    """Test creating a Sport."""

    async def test_creates_sport_with_valid_input(
        self, app: FastAPI, client: AsyncClient, new_sport: SportCreateModel
    ) -> None:
        """Test if a new sport is successfully created with a valid input."""
        res = await client.post(
            app.url_path_for("Create Sport"),
            json=new_sport.dict(),
        )
        assert res.status_code == 200
        
        created_sport = SportCreateModel(**res.json())
        assert created_sport == new_sport
        complete_created_sport = SportPersistModel(**res.json())
        assert complete_created_sport
        assert complete_created_sport.id

    @pytest.mark.parametrize(
        "invalid_payload, status_code",
        (
            (None, 422),
            ({}, 422),
            ({"name": "test_name"}, 422),
            ({"slug": "my-slug"}, 422),
            ({"name": "test_name", "slug": "test"}, 422),
            ({"name": "test_name", "active": True}, 422),
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
        res = await client.post(
            app.url_path_for("Create Sport"),
            json=invalid_payload,
        )
        assert res.status_code == status_code


class TestGetSport:
    """Test getting sport."""

    async def test_get_sport_by_id(
        self, app: FastAPI, client: AsyncClient, new_sport_db_record: SportPersistModel
    ) -> None:
        """Test getting sport by ID."""
        response = await client.get(
            app.url_path_for("Get Sport by id", id=new_sport_db_record.id)
        )

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "invalid_id, status_code",
        (
            (None, 422),
            (-1, 404),
        ),
    )
    async def test_get_sport_by_id_with_nonexistent_id(
        self, app: FastAPI, client: AsyncClient, invalid_id: int, status_code: int
    ) -> None:
        """Test getting a sport with nonexistent id returns 404."""
        response = await client.get(app.url_path_for("Get Sport by id", id=invalid_id))

        assert response.status_code == status_code

    async def test_get_all_sports(
        self, app: FastAPI, client: AsyncClient, new_sport_db_record: SportPersistModel
    ) -> None:
        """Test getting all sports."""
        response = await client.get(app.url_path_for("Get all Sports"))

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

    @pytest.mark.parametrize(
        "filter_name",
        (
            "name",
        ),
    )
    async def test_get_all_sports_by_single_filter(
        self,
        filter_name: str,
        app: FastAPI,
        client: AsyncClient,
        new_sport_db_record: SportPersistModel,
    ) -> None:
        """Test getting sports by using single filters."""
        response = await client.get(
            app.url_path_for("Get all Sports"),
            params={filter_name: getattr(new_sport_db_record, filter_name)},
        )
        assert response.status_code == 200
        assert len(response.json()) > 0
        all_sports = [SportPersistModel(**sport) for sport in response.json()]
        assert all(
            getattr(sport, filter_name) == getattr(new_sport_db_record, filter_name)
            for sport in all_sports
        )
    
    async def test_get_all_sports_with_name_regex_filter(
        self,
        app: FastAPI,
        client: AsyncClient,
    ) -> None:
        """Test getting sports that satisfies filters."""
        # RegEx filter
        any_wonderful = "won.*derf.*"

        # Creating first sport
        response = await client.post(
            app.url_path_for("Create Sport"),
            json=SportCreateModel(
                name="My wonderful sport", slug="some-slug", active=True
            ).dict(),
        )
        assert response.status_code == 200
        first_sport = SportPersistModel(**response.json())

        response = await client.get(
            app.url_path_for("Get all Sports"),
            params={"name": any_wonderful},
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        sport = SportPersistModel(**response.json()[0])
        assert sport == first_sport

        # Creating second sport
        response = await client.post(
            app.url_path_for("Create Sport"),
            json=SportCreateModel(
                name="Another wonderful sport that I like",
                slug="some-other-slug",
                active=False,
            ).dict(),
        )
        assert response.status_code == 200
        second_sport = SportPersistModel(**response.json())

        response = await client.get(
            app.url_path_for("Get all Sports"),
            params={"name": any_wonderful},
        )
        assert response.status_code == 200
        assert len(response.json()) > 0
        all_sports = [SportPersistModel(**sport) for sport in response.json()]
        assert first_sport in all_sports
        assert second_sport in all_sports

    async def test_get_all_sports_by_minimum_active_events(
        self,
        app: FastAPI,
        client: AsyncClient,
        new_sport_db_record: SportPersistModel,
        db: Database,
    ) -> None:
        """Test getting sports by using single filters."""
        response = await client.get(
            app.url_path_for("Get all Sports"),
            params={"active_events_count": 0, "name": new_sport_db_record.name},
        )
        assert response.status_code == 200
        assert len(response.json()) == 0

        # Creating an INACTIVE Event under the Sport
        new_event = EventCreateModel(
            name=generate_random_string(50),
            active=False,
            slug=generate_random_string(40),
            type=EventTypeModel.inplay,
            sport_id=new_sport_db_record.id,
            status=EventStatusModel.pending,
            scheduled_start=datetime.now(),
        )
        event_repository = EventRepository(db)
        event = await event_repository.create_event(new_event=new_event)

        # We should get the same result
        response = await client.get(
            app.url_path_for("Get all Sports"),
            params={"active_events_count": 0, "name": new_sport_db_record.name},
        )
        assert response.status_code == 200
        assert len(response.json()) == 0

class TestUpdateSport:
    """Test updating a Sport."""

    @pytest.mark.parametrize(
        "attributes_to_update, values",
        (
            (["name"], ["My new name"]),
            (["slug"], ["a-nicely-formatted-slug"]),
            (["active"], [False]),
            (
                ["name", "slug", "active"],
                ["Another beautiful name", "some-slug", False],
            ),
        ),
    )
    async def test_updates_sport_with_valid_input(
        self,
        app: FastAPI,
        client: AsyncClient,
        new_sport_db_record: SportPersistModel,
        attributes_to_update: List[str],
        values: List[Any],
    ) -> None:
        """Test if an existing sport is successfully updated with a valid input."""
        values_to_update = {
            attributes_to_update[i]: values[i] for i in range(len(attributes_to_update))
        }

        response = await client.put(
            app.url_path_for("Update Sport", id=new_sport_db_record.id),
            json=values_to_update,
        )

        assert response.status_code == 200
        updated_sport = SportPersistModel(**response.json())
        assert updated_sport.id == new_sport_db_record.id
        # 1. Asserting that every field that should be updated is updated
        for i, attr_to_update in enumerate(attributes_to_update):
            attribute = getattr(updated_sport, attr_to_update)
            assert attribute == values[i]
            assert attribute != getattr(new_sport_db_record, attr_to_update)
        # 2. Asserting that every field that should NOT be updated remains the same
        for attr, value in updated_sport.dict().items():
            if attr not in attributes_to_update:
                assert getattr(new_sport_db_record, attr) == value

    @pytest.mark.parametrize(
        "id, sport_update, status_code",
        (
            (-1, {"name": "A nice name"}, 404),
        ),
    )
    async def test_updates_sport_fails_with_invalid_input(
        self,
        app: FastAPI,
        client: AsyncClient,
        new_sport_db_record: SportPersistModel,
        id: int,
        sport_update: dict,
        status_code: int,
    ) -> None:
        """Test that the update fails if a bad input is given."""
        id = id if id < 0 else new_sport_db_record.id
        response = await client.put(
            app.url_path_for("Update Sport", id=id),
            json=sport_update,
        )
        assert response.status_code == status_code