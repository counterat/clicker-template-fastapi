
from typing import List
from fastapi import HTTPException, Header
from sqlmodel import select
from config import BOTTOKEN
from models import User, UserPublic, UserPublicWithBalances
from schemas import BoostersResponse, ClaimCoinsForTapbot, GetFriendsResponse, TelegramUserSchema, UserPublicExtended
from server.repositories.booster import BoosterRepository
from server.repositories.squad import SquadRepository
from server.repositories.task import TasksRepository
from server.repositories.user import UserRepository
from server.services.game import game_service
from utils.authutils import AuthUtils
from utils.redis_utils import redis_utils


class UserService:
    
    def __init__(self, repo: UserRepository | BoosterRepository | SquadRepository | TasksRepository):
        self.repo = repo
        
    async def tapped_by_tapbot(self, initdata:str):
        user = await self.repo.get_user_or_error(initdata)
        coins_tapped = await redis_utils.get_tapped_by_tapbot(user.id)
        return coins_tapped
    
    async def refill_energy(self, initdata:str):
        user = await self.repo.get_user_or_error(initdata)
        return await self.repo.refill_energy(user_id=user.id)
    
    async def get_friends(self, initdata):
        user = await self.repo.get_user_or_error(initdata, 'invited_users')
        resp = []
        for invited_user in user.invited_users:
            coins_clicked_for_friend = await redis_utils.increment_clicked_for_friend(invited_user.id, 0)
            friend_obj = GetFriendsResponse(
                id=user.id,
                avatar=user.photo_url,
                income=coins_clicked_for_friend,
                nickname=user.name
            )
            resp.append(friend_obj)
        return resp
    
    async def claim_tapped_by_tapbot(self, initdata:str):
        user = await self.repo.get_user_or_error(initdata)
        coins_tapped = await redis_utils.get_tapped_by_tapbot(user.id)
        if coins_tapped:
            coins = await redis_utils.increment_coins(user.id, coins_tapped)
            experience = await redis_utils.increment_experience(user.id, coins_tapped)
            return ClaimCoinsForTapbot(coins=coins, experience=experience)
    
    async def get_leaderboard(self, initdata: str):
        user = await self.repo.get_user_or_error(initdata)
        leaderboard = await redis_utils.get_users_leaderboard()
        leaderboard_resps = []
        all_users_ids_in_leaderboard = [int(leaderboard_pair[0]) for leaderboard_pair in leaderboard]
        all_users = await self.repo.session.scalars(
            select(User).where(User.id.in_(all_users_ids_in_leaderboard))
        )
        all_users = all_users.all()
        all_users = {user.id:user for user in all_users}
        for leaderboard_pair in leaderboard:
            user_id = int(leaderboard_pair[0])
            user = all_users[user_id]
            coins = int(leaderboard_pair[1])
            leaderboard_resp = GetFriendsResponse(
                id = user_id,
                avatar = user.photo_url,
                nickname = user.name,
                income = coins
            )
            leaderboard_resps.append(leaderboard_resp)
            
        return leaderboard_resps
    
    async def authorize(self, initdata: str = Header(..., alias="Authorization")):
        async with self.repo.session.begin():
            is_ok, user_data = AuthUtils.validate_init_data(initdata, BOTTOKEN)
            if not is_ok:
                raise HTTPException(401)
            print(user_data, "user_data")
            user_data =TelegramUserSchema(**user_data)
            if user_data:
                user = await self.repo.get_user_by_attributes(id=user_data.id)
                coins, experience, energy, coins_per_click, maxenergy = None, None, None, None, None
                if not user:
                    user = await self.repo.create_user(user_data)    
                    coins, experience, energy, coins_per_click, maxenergy = await redis_utils.init_user_state(user_data.id)
                else:
                    coins, experience, energy, coins_per_click, maxenergy = await redis_utils.get_user_state(user_data.id)
                
                refills_made = await redis_utils.get_refills_made(user.id)
                balances = {
                    "coins": coins,
                    "experience": experience,
                    "energy": energy,
                    "coins_per_click":coins_per_click,
                    "maxenergy":maxenergy,
                    "refills_made":refills_made
                }
                user_public = self.repo.convert_to_schema(UserPublic, user)
                
                resp = UserPublicExtended(
                    user=user_public,
                    **balances
                )
                phrase = await redis_utils.get_phrase(user.id)
                if not phrase:
                    phrase = await redis_utils.generate_phrase_for_user(user.id)
                    await game_service.send_message_to_player(user.id, {
                        "eventname": "phrase",
                        "phrase": phrase
                    })
                return resp
            raise HTTPException(403)
        
    