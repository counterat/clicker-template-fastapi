from typing import List
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from database import create_session
from models import ShopItem
from schemas import BoostersResponse, BuyBoosterResponse, ShopItemExtended
from server.repositories.booster import BoosterRepository
from server.services.booster import BoosterService
from server.services.user import UserService

router = APIRouter(prefix='/booster')

def get_boosters_service(session: AsyncSession = Depends(create_session)) -> BoosterService:
    repo = BoosterRepository(session)
    return BoosterService(repo)


@router.get("/boosters", response_model=List[BoostersResponse])
async def get_boosters(service: BoosterService = Depends(get_boosters_service), initdata: str = Header(..., alias="Authorization")):
    return await service.get_boosters(initdata)

@router.post("/buy-booster", response_model=BuyBoosterResponse)
async def buy_booster(booster_id:int, service: BoosterService = Depends(get_boosters_service), initdata: str = Header(..., alias="Authorization")):
    return await service.buy_booster(initdata, booster_id=booster_id)
    
@router.get('/shop-items', response_model=List[ShopItemExtended])
async def get_shop_items(service: BoosterService = Depends(get_boosters_service), initdata: str = Header(..., alias="Authorization")):
    return await service.get_shop_items(initdata)

@router.post('/buy-shop-item', response_model=str)
async def buy_shop_item(shop_item_id:int, service: BoosterService = Depends(get_boosters_service), initdata: str = Header(..., alias="Authorization")):
    return await service.buy_shop_item(initdata, shop_item_id)