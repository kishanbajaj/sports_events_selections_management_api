from typing import List
from datetime import datetime, timezone

from app.db.repository.base import BaseRepository
from app.db.repository.sports import SportRepository
from app.schemas.event import EventCreateModel, EventPersistModel, EventStatusModel, EventUpdateModel

create_query = "INSERT INTO event (name, slug, active, type, sport_id, status, scheduled_start, actual_start) " \
    "VALUES (:name, :slug, :active, :type, :sport_id, :status, :scheduled_start, :actual_start) " \
    "RETURNING *"

get_query = "SELECT * FROM event"

get_by_id_query = "SELECT * FROM event WHERE ID = :id"

update_query = "UPDATE event " \
    "SET name = :name, " \
    "slug = :slug, " \
    "active = :active, " \
    "type = :type, " \
    "sport_id = :sport_id, " \
    "status = :status, " \
    "scheduled_start = :scheduled_start, " \
    "actual_start = :actual_start " \
    "WHERE id = :id " \
    "RETURNING *"

update_actual_start_query = "UPDATE event " \
    "SET actual_start = :actual_start " \
    "WHERE id = :id " \
    "RETURNING *"

check_active_event_query = "SELECT EXISTS " \
    "(SELECT 1 FROM event WHERE sport_id = :sport_id AND active = true)"


class EventRepository(BaseRepository):
    async def create_event(self, *, new_event: EventCreateModel) -> EventPersistModel:
        
        if new_event.status == EventStatusModel.started:
            new_event.actual_start = datetime.now(timezone.utc)
        
        query_values = new_event.dict()
        event = await self.db.fetch_one(query=create_query, values=query_values)
        
        if not dict(event)["active"]:
            active_event = await self.db.fetch_one(query=check_active_event_query,values={"sport_id": dict(event)["sport_id"]}) 
            if not dict(active_event)["exists"]:
                sports_repository = SportRepository(self.db)
                await sports_repository.update_sport_inactive(id=dict(event)["sport_id"])


        return event

    async def get_all_events(self, search_filters: dict) -> List[EventPersistModel]:
        
        search_query = get_query
        filter_conditions = []
        
        for key, val in search_filters.items():
            if val is not None:
                if key == "name":
                    filter_conditions.append(key + " ~* " + "'" + val + "'")
                elif key == "active_selections_count":
                    filter_conditions.append("id IN (SELECT event_id FROM selection WHERE active = true GROUP BY event_id HAVING count(*) >= " + str(val) + ")")
        
        if filter_conditions:
            search_query += " where " + " and ".join(filter_conditions)
        
        search_result = await self.db.fetch_all(query=search_query)
        return [event for event in search_result]


    async def get_event_by_id(self, *, id: int) -> EventPersistModel:
        event = await self.db.fetch_one(query=get_by_id_query, values={"id": id})       
        if not event:
            return None
        return event


    async def update_event(self, *, id: int, event_update: EventUpdateModel) -> EventPersistModel:
        event = await self.get_event_by_id(id=id)

        if not event:
            return None

        if event_update.status == EventStatusModel.started:
            event_update.actual_start = datetime.now(timezone.utc)

        update_dict = dict(event).copy()

        for key, val in event_update.dict().items():
            if val is not None:
                update_dict[key] = event_update.dict()[key]

        update_result = await self.db.fetch_one(query=update_query, values=update_dict)
        
        if not dict(update_result)["active"]:
            active_event = await self.db.fetch_one(query=check_active_event_query,values={"sport_id": dict(event)["sport_id"]}) 
            if not dict(active_event)["exists"]:
                sports_repository = SportRepository(self.db)
                await sports_repository.update_sport_inactive(id=dict(event)["sport_id"])
        
        return update_result     


    async def update_event_inactive(self, id: int) -> None:
        event_inactive = EventUpdateModel()
        event_inactive.active = False
        await self.update_event(id=id, event_update=event_inactive)  