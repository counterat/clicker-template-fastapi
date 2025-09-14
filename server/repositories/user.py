from sqlalchemy import select, func, update
from database import get_session, AsyncSession
from sqlmodel import SQLModel
from models import BoosterItem, ShopItem, User, UserPublic, UserPublicWithBalances, UserShopItem
from fastapi import HTTPException, Header
from aiogram import types
from config import BOTTOKEN, BOTURL
from typing import Any, Optional
from sqlalchemy.orm import selectinload
from schemas import RefillEnergyResponse, TelegramUserSchema
from utils.authutils import AuthUtils
from utils.redis_utils import redis_utils


class UserRepository:
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
    def convert_to_schema(self, schema_cls: type[SQLModel], model_obj: SQLModel) -> SQLModel:
        return schema_cls.model_validate(model_obj)

    async def get_user_or_error(self, initdata: str = Header(..., alias="Authorization"), *joins) -> User:
            try:
                tg_data = (AuthUtils.validate_init_data(initdata, BOTTOKEN))[1]
                tg_user = TelegramUserSchema(**tg_data)
            except Exception:
                raise HTTPException(status_code=401, detail="Invalid Authorization")

            user = await self.get_user_by_attributes(*joins, id=tg_user.id)
            
            if not user:
                raise HTTPException(401, 'You need to be registered to access that endpoint')
            elif user.is_deleted:
                raise HTTPException(403, 'You are banned')
            
            return user
    
    async def get_user_by_attributes(self, *joins, **filters: Any) -> Optional[User]:
        conditions = [
            getattr(User, key) == value for key, value in filters.items()
        ]
        loader_options  = [
            selectinload(getattr(User, join)) for join in joins
        ]
        stmt = select(User).where(*conditions).options(*loader_options)
        result = await self.session.scalar(stmt)
        return result
    
    async def get_all_boosters(self):
        boosters = await self.session.scalars(
            select(BoosterItem)
        )
        boosters = boosters.all()
        return boosters
    
    async def refill_energy(self, user_id: int):
        #coins = await redis_utils.get_user_coins(user_id)
        refills_made = await redis_utils.change_refills_made(user_id)
        if refills_made:
            max_energy = await redis_utils.get_maxenergy(user_id=user_id)
            energy = await redis_utils.increment_energy(user_id, max_energy, is_set=True)
            return RefillEnergyResponse(refills_made=refills_made, energy=max_energy)
        raise HTTPException(400, 'You have exceeded refills limit')
    async def give_default_skin(self, user: User):
        default_skin = await self.session.scalar(
            select(ShopItem).where(ShopItem.price == 0)
        )
        user_skin = UserShopItem(
            shop_item_id=default_skin.id,
            user_id=user.id,
            is_equipped=True
        )
        self.session.add(user_skin)
            
    async def create_user(self, user_data: TelegramUserSchema | types.User, invited_by_arg: Optional[int|str] = None):
        user = None
        invited_by = None
        
        if invited_by_arg:
            invited_by = await self.get_user_by_attributes(id = invited_by_arg)
            if invited_by:
                prize = 20_000 if user_data.is_premium else 10_000
                await redis_utils.increment_coins(invited_by.id, prize)
            
        if type(user_data) == TelegramUserSchema:  
            
            user = User(
                id = user_data.id,
                name = user_data.first_name + user_data.last_name,
                username = user_data.username,
                photo_url = user_data.photo_url,
                language_code = user_data.language_code,
                invited_by = invited_by_arg if invited_by else None,
                invite_link = f'{BOTURL}/?start={user_data.id}'
            )
            
        elif type(user_data) == types.User:
            user = User(
                name = user_data.id,
                username= user_data.username,
                language_code = user_data.language_code,
                invited_by = invited_by
            )
        
        self.session.add(user)
        await self.session.flush()
        await self.give_default_skin(user)
        
        return user
            
            