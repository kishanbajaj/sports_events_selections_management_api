import json
from typing import Any, List

import pytest

from databases import Database
from fastapi import FastAPI
from httpx import AsyncClient
from app.db.repository.events import EventRepository
from app.db.repository.selections import SelectionRepository
from app.db.repository.sports import SportRepository
from app.schemas.selection import SelectionCreateModel, SelectionPersistModel, SelectionOutcomeModel

from tests.utils import generate_random_string

pytestmark = pytest.mark.asyncio


class TestSelectionRoutes:
    """Tests for the /selections route."""

    @pytest.mark.asyncio
    async def test_route_exist(self, app: FastAPI, client: AsyncClient) -> None:
        """Test that the route exists."""
        res = await client.post(app.url_path_for("Create Selection"), json={})
        assert res.status_code != 404

    @pytest.mark.asyncio
    async def test_invalid_input_raises_error(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        """Test if an invalid input raises error"""
        res = await client.post(app.url_path_for("Create Selection"), json={})
        assert res.status_code == 422


class TestCreateSelection:
    """Test creating an Selection."""

    async def test_creates_selection_with_valid_input(
        self, app: FastAPI, client: AsyncClient, new_selection: SelectionCreateModel
    ) -> None:
        """Test if a new selection is successfully created with a valid input."""
        response = await client.post(
            app.url_path_for("Create Selection"),
            json=new_selection.dict(),
        )
        assert response.status_code == 200
        creted_selection = SelectionCreateModel(**response.json())
        assert creted_selection == new_selection
        complete_created_selection = SelectionPersistModel(**response.json())
        assert complete_created_selection
        assert complete_created_selection.id

    @pytest.mark.parametrize(
        "invalid_payload, status_code",
        (
            (None, 422),
            ({}, 422),
            ({"name": "test_name"}, 422),
            ({"name": "test_name", "event_id": -1}, 422),
            ({"name": "test_name", "price": 3.99}, 422),
            ({"name": "test_name", "outcome": "invalid"},422),
            ({"name": "test_name", "active": True, "price": 5.44},422),
            ({"name": "", "active": True, "price": 5.44},422),
            ({"name": generate_random_string(101),"active": True,"price": 5.44},422),
            ({"name": generate_random_string(101),"event_id": -1,"price": 5.44},422),
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
            app.url_path_for("Create Selection"),
            json=invalid_payload,
        )
        assert res.status_code == status_code


class TestGetSelection:
    """Test getting selection."""

    async def test_get_selection_by_id(
        self, app: FastAPI, client: AsyncClient, new_selection_db_record: SelectionPersistModel
    ) -> None:
        """Test getting selection by ID."""
        response = await client.get(
            app.url_path_for("Get Selection by id", id=new_selection_db_record.id)
        )

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "invalid_id, status_code",
        (
            (None, 422),
            (-1, 404),
        ),
    )
    async def test_get_selection_by_id_with_nonexistent_id(
        self, app: FastAPI, client: AsyncClient, invalid_id: int, status_code: int
    ) -> None:
        """Test getting an selection with nonexistent id returns 404."""
        response = await client.get(
            app.url_path_for("Get Selection by id", id=invalid_id)
        )

        assert response.status_code == status_code

    async def test_get_all_selections(
        self, app: FastAPI, client: AsyncClient, new_selection_db_record: SelectionPersistModel
    ) -> None:
        """Test getting all selections."""
        response = await client.get(app.url_path_for("Get all Selections"))

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

    @pytest.mark.parametrize(
        "filter_name",
        (
            "name",
        ),
    )
    async def test_get_all_selections_by_single_filter(
        self,
        filter_name: str,
        app: FastAPI,
        client: AsyncClient,
        new_selection_db_record: SelectionPersistModel,
    ) -> None:
        """Test getting selections by using single filters."""
        filter_value = getattr(new_selection_db_record, filter_name, None)

        if filter_name == "outcome":
            filter_value = filter_value.value

        response = await client.get(
            app.url_path_for("Get all Selections"),
            params={filter_name: filter_value},
        )
        assert response.status_code == 200
        assert len(response.json()) > 0
        all_selections = [SelectionPersistModel(**selection) for selection in response.json()]
        assert all(
            getattr(selection, filter_name)
            == getattr(new_selection_db_record, filter_name)
            for selection in all_selections
            if filter_name in SelectionPersistModel.__fields__.keys()
        )

    async def test_get_all_selections_by_multiple_filters(
        self,
        app: FastAPI,
        client: AsyncClient,
        new_selection_db_record: SelectionPersistModel,
    ) -> None:
        """Test getting selections by using multiple filters."""
        response = await client.get(
            app.url_path_for("Get all Selections"),
            params={
                "name": new_selection_db_record.name,
            },
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

    async def test_get_all_selections_with_name_regex_filter(
        self, app: FastAPI, client: AsyncClient, new_event_db_record: SelectionPersistModel
    ) -> None:
        """Test getting selections that satisfies filters."""
        # RegEx filter
        odds_for_Real_Madrid = "O.*Madr.*"

        # Creating first selection
        response = await client.post(
            app.url_path_for("Create Selection"),
            json=json.loads(
                SelectionCreateModel(
                    name="Odds for Real Madrid",
                    active=True,
                    event_id=new_event_db_record.id,
                    price=599.99,
                    outcome=SelectionOutcomeModel.lose,
                ).json()
            ),
        )
        assert response.status_code == 200
        first_selection = SelectionPersistModel(**response.json())

        response = await client.get(
            app.url_path_for("Get all Selections"),
            params={"name": odds_for_Real_Madrid},
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        selection = SelectionPersistModel(**response.json()[0])
        assert selection == first_selection

        # Creating second selection
        response = await client.post(
            app.url_path_for("Create Selection"),
            json=json.loads(
                SelectionCreateModel(
                    name="Odds for Real Madrid",
                    active=False,
                    event_id=new_event_db_record.id,
                    price=22.66,
                    outcome=SelectionOutcomeModel.win,
                ).json()
            ),
        )
        assert response.status_code == 200
        second_selection = SelectionPersistModel(**response.json())

        response = await client.get(
            app.url_path_for("Get all Selections"),
            params={"name": odds_for_Real_Madrid},
        )
        assert response.status_code == 200
        assert len(response.json()) > 0
        all_selections = [SelectionPersistModel(**selection) for selection in response.json()]
        assert first_selection in all_selections
        assert second_selection in all_selections


class TestUpdateSelections:
    """Test updating a selection."""

    @pytest.mark.parametrize(
        "attributes_to_update, values",
        (
            (["name"], ["My new name"]),
            (["active"], [False]),
            (["event_id"], [1]),
            (["price"], [18.25]),
            (["outcome"], [SelectionOutcomeModel.void.value]),
        ),
    )
    async def test_updates_selection_with_valid_input(
        self,
        app: FastAPI,
        client: AsyncClient,
        new_selection_db_record: SelectionPersistModel,
        attributes_to_update: List[str],
        values: List[Any],
    ) -> None:
        """Test if an existing selection is successfully updated with a valid input."""
        values_to_update = {
            attributes_to_update[i]: values[i] for i in range(len(attributes_to_update))
        }

        response = await client.put(
            app.url_path_for("Update Selection", id=new_selection_db_record.id),
            json=values_to_update,
        )

        assert response.status_code == 200
        updated_selection = SelectionPersistModel(**response.json())
        assert updated_selection.id == new_selection_db_record.id
        # 1. Asserting that every field that should be updated is updated
        for i, attr_to_update in enumerate(attributes_to_update):
            attribute = getattr(updated_selection, attr_to_update)
            assert attribute == values[i]
            assert attribute != getattr(new_selection_db_record, attr_to_update)

    @pytest.mark.parametrize(
        "id, selection_update, status_code",
        (
            (1, {"outcome": "invalid enum"}, 422),
            (1, {"event_id": -1}, 404),
            (-1, {"name": "A nice name"}, 404),
        ),
    )
    async def test_updates_selection_fails_with_invalid_input(
        self,
        app: FastAPI,
        client: AsyncClient,
        new_selection_db_record: SelectionPersistModel,
        id: int,
        selection_update: dict,
        status_code: int,
    ) -> None:
        """Test that the update fails if a bad input is given."""
        id = id if id < 0 else new_selection_db_record.id

        response = await client.put(
            app.url_path_for("Update Selection", id=id),
            json=selection_update,
        )
        assert response.status_code == status_code

    async def test_event_inactive_when_the_only_active_selection_is_updated_to_inactive(
        self,
        app: FastAPI,
        client: AsyncClient,
        db: Database,
        new_selection_db_record: SelectionPersistModel,
    ) -> None:
        """Test if the event will be inactivated when the only active selection becomes inactive."""
        # Creating one more event under the same sport
        selection_repository = SelectionRepository(db)
        selection_create = SelectionCreateModel(**new_selection_db_record)
        selection_create.name = "new name"
        second_selection = await selection_repository.create_selection(
            new_selection=selection_create
        )
        assert second_selection

        # Checking that the event is active
        event_repository = EventRepository(db)
        event = await event_repository.get_event_by_id(
            id=new_selection_db_record.event_id
        )
        assert event.active is True

        # Deactivating the first selection
        response = await client.put(
            app.url_path_for("Update Selection", id=new_selection_db_record.id),
            json={"active": False},
        )
        assert response.status_code == 200
        event = await event_repository.get_event_by_id(
            id=new_selection_db_record.event_id
        )
        assert event.active is True
        # Deactivating the second selection
        response = await client.put(
            app.url_path_for("Update Selection", id=second_selection.id),
            json={"active": False},
        )
        
        # Now the event should be inactive
        event = await event_repository.get_event_by_id(
            id=new_selection_db_record.event_id
        )
        assert event.active is False
        # And the Sport should be inactive as well
        sport_respository = SportRepository(db)
        sport = await sport_respository.get_sport_by_id(id=event.sport_id)
        assert sport.active is False