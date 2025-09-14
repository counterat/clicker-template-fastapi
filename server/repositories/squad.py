from aiogram import session
from sqlalchemy import delete, select
from bot.main import get_chat_info
from models import Squad, User, UserSquad
from server.repositories.user import UserRepository
from utils.botutils import download_squad_icon
from utils.redis_utils import redis_utils


class SquadRepository(UserRepository):
    
    async def get_squad_by_link(self, link: str):
        squad = await self.session.scalar(
            select(Squad).where(Squad.link_to_squad == link)
        )
        return squad
    
    async def create_squad(self, link: str, founder: User):
        photo_url, title, chat_id = await get_chat_info(link)
        photo_url = await download_squad_icon(photo_url, chat_id)
        squad = Squad(
            id=chat_id,
            founder_id=founder.id,
            link_to_squad=link,
            title=title,
            photo_url="/"+photo_url
        )
        self.session.add(squad)
        await self.session.flush()
        await redis_utils.incr_squad_coins(squad.id, coins=0)
        await self.create_new_user_squad_row(founder, squad.id)
        return squad
        
    async def sort_squads_by_coins_clicked(self):
        pass

    async def get_squad(self, squad_id: int):
        squad = await self.session.scalar(
            select(Squad).where(Squad.id == squad_id)
        )
        return squad

    async def leave_squad(self, user: User):
        if user.user_squad:
            q = delete(UserSquad).where(UserSquad.id == user.user_squad.id)
            await self.session.execute(q)
            
    async def create_new_user_squad_row(self, user:User, squad_id: int):
        user_squad_row = UserSquad(
            user_id=user.id,
            squad_id=squad_id
        )
        self.session.add(user_squad_row)
        await self.session.flush()
        await self.session.refresh(user, attribute_names=["user_squad"])
        await redis_utils.set_in_squad(user.id, squad_id)
        return user, user_squad_row