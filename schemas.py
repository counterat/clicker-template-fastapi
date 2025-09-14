from re import S
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from models import BoosterItem, ShopItem, Squad, Task, UserPublic


class ShopItemExtended(BaseModel):
    item: ShopItem
    is_equipped: bool
    is_owned: bool

class UserPublicExtended(BaseModel):
    user: UserPublic
    coins: Optional[int]
    experience: Optional[int]
    energy: Optional[int]
    coins_per_click: Optional[int]
    refills_made: Optional[int]
    maxenergy: Optional[int]

class TelegramUserSchema(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    name: Optional[str] = None
    photo_url: Optional[str] = None
    is_premium: Optional[bool] = False


class BoostersResponse(BaseModel):
    booster: BoosterItem
    is_equipped: bool
    level: Optional[int]

class BuyBoosterResponse(BaseModel):
    coins_per_click: Optional[int]
    maxenergy: Optional[int]
    coins_per_click: Optional[int]
    coins: int
    user_booster_item: BoostersResponse
    
class ClaimCoinsForTapbot(BaseModel):
    coins: int
    experience: int
    
class RefillEnergyResponse(BaseModel):
    refills_made: int
    energy: int
    
class GetFriendsResponse(BaseModel):
    id: int
    avatar: str
    nickname: str
    income: int
    
class SquadLeadeboardResponse(BaseModel):
    squad: Squad
    coins: int
    
class TaskResponse(BaseModel):
    task: Task
    is_completed: bool
    