from typing import List

from app.db.repository.base import BaseRepository
from app.db.repository.events import EventRepository
from app.schemas.selection import SelectionCreateModel, SelectionPersistModel, SelectionUpdateModel

create_query = "INSERT INTO selection (name, event_id, price, active, outcome) " \
    "VALUES (:name, :event_id, :price, :active, :outcome) " \
    "RETURNING *"

get_query = "SELECT * FROM selection"

get_by_id_query = "SELECT * FROM selection WHERE ID = :id"

update_query = "UPDATE selection " \
    "SET name = :name, " \
    "active = :active, " \
    "event_id = :event_id, " \
    "price = :price, " \
    "outcome = :outcome " \
    "WHERE id = :id " \
    "RETURNING *"

check_active_selection_query = "SELECT EXISTS " \
    "(SELECT 1 FROM selection WHERE event_id = :event_id AND active = true)"

class SelectionRepository(BaseRepository):

    async def create_selection(self, *, new_selection: SelectionCreateModel) -> SelectionPersistModel:
        query_values = new_selection.dict()
        selection = await self.db.fetch_one(query=create_query, values=query_values)
        if not dict(selection)["active"]:
            active_selection = await self.db.fetch_one(query=check_active_selection_query,values={"event_id": dict(selection)["event_id"]})  
            if not dict(active_selection)["exists"]:
                events_repository = EventRepository(self.db)
                await events_repository.update_event_inactive(id=dict(selection)["event_id"])

        return selection

    async def get_all_selections(self, search_filters: dict) -> List[SelectionPersistModel]:

        search_query = get_query
        filter_conditions = []
        
        for key, val in search_filters.items():
            if val:
                if key == "name":
                    filter_conditions.append(key + " ~* " + "'" + val + "'")

        if filter_conditions:
            search_query += " where " + " and ".join(filter_conditions)
        
        search_result = await self.db.fetch_all(query=search_query)
        return [selection for selection in search_result]


    async def get_selection_by_id(self, *, id: int) -> SelectionPersistModel:
        selection = await self.db.fetch_one(query=get_by_id_query, values={"id": id})
        if not selection:
            return None
        return selection

    async def update_selection(self, *, id: int, selection_update: SelectionUpdateModel) -> SelectionPersistModel:
        selection = await self.get_selection_by_id(id=id)

        if not selection:
            return None

        update_dict = dict(selection).copy()

        for key, val in selection_update.dict().items():
            if val is not None:
                update_dict[key] = selection_update.dict()[key]

        update_result = await self.db.fetch_one(query=update_query, values=update_dict)
        
        if not dict(update_result)["active"]:

            active_selection = await self.db.fetch_one(query=check_active_selection_query,values={"event_id": dict(selection)["event_id"]})  
            if not dict(active_selection)["exists"]:

                events_repository = EventRepository(self.db)
                await events_repository.update_event_inactive(id=dict(selection)["event_id"])
        
        return update_result 