
from typing import Dict
from fastapi import HTTPException
from sqlalchemy import select
from models import Squad
from schemas import SquadLeadeboardResponse
from server.services.user import UserService
from utils.redis_utils import redis_utils


class SquadService(UserService):
    
    async def create_squad(self, link:str, initdata:str):
        async with self.repo.session.begin():
            user = await self.repo.get_user_or_error(initdata, "user_squad")
            squad_with_same_link = await self.repo.get_squad_by_link(link)
            if squad_with_same_link:
                raise HTTPException(400, "There squad with this link is already exists")
            await self.repo.leave_squad(user)
            return await self.repo.create_squad(link, user)
            
    async def get_squads(self, initdata: str):
        user = await self.repo.get_user_or_error(initdata)
        sorted_squads_by_coins: Dict[int, int] = await redis_utils.get_sorted_squads_by_coins()
        squad_ids = sorted_squads_by_coins.keys()
        squads = await self.repo.session.scalars(
            select(Squad).where(Squad.id.in_(squad_ids))
        )
        squads = squads.all()
        resp = [SquadLeadeboardResponse(squad=squad, coins=sorted_squads_by_coins[squad.id]) for squad in squads]
        return resp
        
    async def join_squad(self, initdata: str, squad_id: int):
        async with self.repo.session.begin():
            user = await self.repo.get_user_or_error(initdata, "user_squad")
            squad = await self.repo.get_squad(squad_id)
            if not squad:
                raise HTTPException(404, 'There is no such squad')
            
            if user.user_squad:
                await self.repo.leave_squad(user)
            user, user_squad_row = await self.repo.create_new_user_squad_row(user, squad_id)
            return user_squad_row
    
    async def get_my_squad(self, initdata: str):
        user = await self.repo.get_user_or_error(initdata, "user_squad")
        if user.user_squad:
            return user.user_squad.squad_id