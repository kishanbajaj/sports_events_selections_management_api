from typing import List

from app.db.repository.base import BaseRepository
from app.schemas.sport import SportCreateModel, SportPersistModel, SportUpdateModel

create_query = "INSERT INTO sport (name, slug, active) " \
    "VALUES (:name, :slug, :active) " \
    "RETURNING id, name, slug, active"

get_by_id_query = "SELECT * FROM sport WHERE ID = :id"

get_query = "SELECT * FROM sport"

update_query = "UPDATE sport " \
    "SET name = :name, slug = :slug, active = :active " \
    "WHERE id = :id "\
    "RETURNING *"

class SportRepository(BaseRepository):

    async def create_sport(self, *, new_sport: SportCreateModel) -> SportPersistModel:
        query_values = new_sport.dict()
        sport = await self.db.fetch_one(query=create_query, values=query_values)
        return sport


    async def get_sport_by_id(self, *, id: int) -> SportPersistModel:
        sport = await self.db.fetch_one(query=get_by_id_query, values={"id": id})
        if not sport:
            return None
        return sport

    async def get_all_sports(self, search_filters: dict) -> List[SportPersistModel]:
        
        search_query = get_query
        filter_conditions = []
        for key, val in search_filters.items():
            if val is not None:
                if key == "name":
                    filter_conditions.append(key + " ~* " + "'" + val + "'")
                elif key == "active_events_count":
                    filter_conditions.append("id IN (SELECT sport_id FROM event WHERE active = true GROUP BY sport_id HAVING count(*) >= " + str(val) + ")")
        
        if filter_conditions:
            search_query += " where " + " and ".join(filter_conditions)
        print(search_query)
        search_result = await self.db.fetch_all(query=search_query)
        return [sport for sport in search_result]


    async def update_sport(self, *, id: int, sport_update: SportUpdateModel) -> SportPersistModel:
        sport = await self.get_sport_by_id(id=id)

        if not sport:
            return None

        update_dict = dict(sport).copy()

        for key, val in sport_update.dict().items():
            if val is not None:
                update_dict[key] = sport_update.dict()[key]

        update_result = await self.db.fetch_one(query=update_query, values=update_dict)
        return update_result

    async def update_sport_inactive(self, id: int) -> None:
        sport_inactive = SportUpdateModel()
        sport_inactive.active = False
        await self.update_sport(id=id, sport_update=sport_inactive)