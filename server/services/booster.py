import json
import math
from typing import List

from aiogram import session, types
from fastapi import HTTPException
from sqlalchemy import select
from bot.main import bot
from models import BoosterItem, Invoice, User
from schemas import BoostersResponse, BuyBoosterResponse, ShopItemExtended
from server.services.user import UserService
from utils.redis_utils import redis_utils


class BoosterService(UserService):
    
    async def buy_shop_item(self, initdata: str, shop_item_id: int):
        async with self.repo.session.begin():
            user = await self.repo.get_user_or_error(initdata, 'shop_items')
            owned_shop_items_ids = [shop_item.shop_item_id for shop_item in user.shop_items]
            if shop_item_id in owned_shop_items_ids:
                raise HTTPException(400, 'You already own this Skin!')
            shop_item = await self.repo.get_shop_item(shop_item_id)
            invoice = Invoice(
                user_id=user.id,
                shop_item_id=shop_item.id,
                price=shop_item.price
            )
            
            link = await bot.create_invoice_link(
                title=f"{shop_item.name.capitalize()}",
                description="Skin that help you to earn money",
                prices=[types.LabeledPrice(label=f"{shop_item.name}", amount=invoice.price)],
                provider_token="",
                payload=json.dumps({
                    "payment_id":invoice.id
                }),
                currency="XTR"
            )
            return link
            
    
    async def get_shop_items(self, initdata: str):
        user: User = await self.repo.get_user_or_error(initdata, "shop_items")
        owned_skin_ids = [skin.shop_item_id for skin in user.shop_items]
        equipped_skin_ids = [skin.shop_item_id for skin in user.shop_items if skin.is_equipped]
        shop_items = await self.repo.get_all_shop_items()
        
        resp = []
        for shop_item in shop_items:
            resp.append(
                ShopItemExtended(
                    item=shop_item,
                    is_owned=shop_item.id in owned_skin_ids,
                    is_equipped=shop_item.id in equipped_skin_ids
                )
            )
        
        return resp
    
    async def buy_booster(self, initdata:str, booster_id: int):
        async with self.repo.session.begin():
            user = await self.repo.get_user_or_error(initdata, 'boosters')
            owned_boosters_ids = [user_booster.booster_id for user_booster in user.boosters]
            coins = await redis_utils.get_user_coins(user.id)
            booster_item = await self.repo.get_booster(booster_id)
            level_of_booster = owned_boosters_ids.count(booster_item.id)
            price = int(booster_item.price) * math.pow(2, level_of_booster)
            
            if coins >= price:
                extra_info, coins, user_booster_item = await self.repo.buy_booster(booster_item, user, price)
                coins_per_click = extra_info.get("coins_per_click")
                boosters_response = BoostersResponse(
                    booster=booster_item,
                    is_equipped=True,
                    level=level_of_booster+1
                )
                buy_boosters_response = BuyBoosterResponse(coins=coins,
                    user_booster_item=boosters_response,
                    coins_per_click=coins_per_click,
                    maxenergy=extra_info.get("maxenergy")
                )
                
                return buy_boosters_response
            raise HTTPException(400, 'Not enough coins') 
                
    async def get_boosters(self, initdata: str) -> List[BoostersResponse]:
        user = await self.repo.get_user_or_error(initdata, "boosters")
        owned_boosters_ids = [user_booster.booster_id for user_booster in user.boosters]
        all_boosters = await self.repo.get_all_boosters()
        boosters_resp = []
        for booster in all_boosters:
            
            booster_resp = BoostersResponse(
                booster=booster,
                is_equipped=booster.id in owned_boosters_ids,
                level=owned_boosters_ids.count(booster.id)
            )
            
            
            boosters_resp.append(
                booster_resp
            )
        return boosters_resp
    