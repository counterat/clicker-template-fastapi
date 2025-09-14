import traceback
from database import AsyncSession
from sqlalchemy import exc, select, update, func, desc, or_
from models import User
from typing import Any, Optional, List
from schemas import TelegramUserSchema
from database import get_session
from config import BOTTOKEN, ENERGY_REFILLS
from server.services.game import game_service
from utils.authutils import AuthUtils
from fastapi import Header, HTTPException, status, WebSocketDisconnect, WebSocket

from sqlalchemy.orm import selectinload

from sqlmodel import SQLModel
from datetime import datetime, timedelta

from utils.redis_utils import RedisUtils, redis_utils


class GameRepository:
    
    @staticmethod
    async def send_phrases():
        async with get_session() as session:
            session: AsyncSession
            all_user_ids = await session.scalars(
                select(User.id)
            )
            all_user_ids = all_user_ids.all()
            for user_id in all_user_ids:

                    phrase = await redis_utils.generate_phrase_for_user(user_id)
                    await game_service.send_message_to_player(user_id, {
                        "eventname": "phrase",
                        "phrase": phrase
                    })

    
    @staticmethod
    async def give_10_percents_of_income_to_invited_by():
        all_users_invited_by = await redis_utils.get_all_users_invited_by()
        for user_id, invited_by in all_users_invited_by.items():
            if invited_by:
                clicked_today = await redis_utils.get_clicked_today(user_id)
                if clicked_today:
                    tax = int(clicked_today * 0.1)
                    await redis_utils.increment_coins(invited_by, tax)
                    await redis_utils.increment_clicked_today(user_id, -clicked_today)
    
    @staticmethod
    async def regenerate_energy():
        all_energy_rows = await redis_utils.get_all_energy_rows()
        for user_id, energy in all_energy_rows.items():
            maxenergy = await redis_utils.get_maxenergy(user_id)
            if energy < maxenergy:
                difference = maxenergy - energy
                if difference > ENERGY_REFILLS:
                    await redis_utils.increment_energy(user_id, ENERGY_REFILLS)
                else:
                    await redis_utils.increment_energy(user_id, difference)
    
    @staticmethod
    async def click_for_tapbots():
        all_tapbots = await redis_utils.get_all_tapbots()
        for user_id, coins_clicked in all_tapbots.items():
            coins_per_click = await redis_utils.get_coins_per_click(user_id)
            await redis_utils.increment_tapbot(user_id, coins_per_click*60)
            await redis_utils.increment_tapped_by_tapbot(user_id, coins_per_click*60)
            
    
    @staticmethod
    async def get_user_or_error(websocket: WebSocket, initdata: str = Header(..., alias="Authorization"), *joins, session: Optional[AsyncSession] = None) -> User:
        if not session:
            async with get_session() as session:
                session: AsyncSession
            try:
                tg_data = (AuthUtils.validate_init_data(initdata, BOTTOKEN))[1]
                tg_user = TelegramUserSchema(**tg_data)
            except Exception:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION) 

            user = await GameRepository.get_user_by_attributes(session, *joins, id=tg_user.id)
            
            if not user:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION) 
            elif user.is_deleted:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION) 
            
            return user
        else:
            session: AsyncSession
            try:
                tg_data = (AuthUtils.validate_init_data(initdata, BOTTOKEN))[1]
                tg_user = TelegramUserSchema(**tg_data)
            except Exception:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION) 

            user = await GameRepository.get_user_by_attributes(session, *joins, id=tg_user.id)
            
            if not user:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION) 

            elif user.is_deleted:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                raise WebSocketDisconnect(code=status.WS_1008_POLICY_VIOLATION) 

            return user

    @staticmethod
    async def get_user_by_attributes(session: AsyncSession, *joins, **filters: Any) -> Optional[User]:
        conditions = [
            getattr(User, key) == value for key, value in filters.items()
        ]
        loader_options  = [
            selectinload(getattr(User, join)) for join in joins
        ]
        stmt = select(User).where(*conditions).options(*loader_options)
        result = await session.scalar(stmt)
        return result

    @staticmethod
    async def send_message_to_player(player_id: int, message):
        ws = game_service.game_subscribers.get(player_id)
        if ws:
            try:
                await ws.send_json((message))
            except Exception as e:
                traceback.print_exc()
                
    @staticmethod
    async def tap_handler(websocket: WebSocket, user:User, clicks: int, phrase:str, initdata: str = Header(..., alias="Authorization")):
        async with get_session(transaction=True) as session:
            if clicks > 20:
                raise Exception("Too many clicks at once")
            
            
            is_valid_phrase = await redis_utils.is_valid_phrase(user_id=user.id, phrase=phrase)
            
            if not is_valid_phrase:
                raise HTTPException(403)        
            
            is_human_clicking = await redis_utils.is_human_clicking(user.id)
            if is_human_clicking:
                energy, coins, exp, coins_per_click = await redis_utils.change_state_by_clicks(user.id, clicks)
                await redis_utils.increment_clicked_today(user.id, coins_per_click)
                
                return energy, coins, exp
                    
            