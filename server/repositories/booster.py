from sqlalchemy import select
from models import BoosterItem, ShopItem, User, UserBooster
from server.repositories.user import UserRepository
from utils.redis_utils import redis_utils



class BoosterRepository(UserRepository):
    
    
    
    async def get_shop_item(self, shop_item_id: int):
        shop_item = await self.session.scalar(
            select(ShopItem).where(ShopItem.id == shop_item_id)
        )
        return shop_item
    
    async def get_booster(self, booster_id: int):
        booster = await self.session.scalar(
            select(BoosterItem).where(BoosterItem.id == booster_id)
        )
        return booster
    
    async def get_all_shop_items(self):
        all_shop_items = await self.session.scalars(
            select(ShopItem)
        )
        all_shop_items = all_shop_items.all()
        return all_shop_items
    
    
    async def buy_booster(self, booster: BoosterItem, user: User, price: int):
        coins = await redis_utils.decrement_coins(user.id, price)
        user_booster_item = UserBooster(
            booster_id=booster.id,
            user_id=user.id,
            is_equipped=True
        )
        extra_info = {}
        if booster.name == 'multitap':
            coins_per_click = await redis_utils.increment_coins_per_click(user.id, 1)
            extra_info['coins_per_click'] = coins_per_click
            
        elif booster.name == 'tapbot':
            tapbot = await redis_utils.get_tapbot(user.id)
            if not tapbot:
                await redis_utils.create_tapbot(user.id)
            
        elif booster.name == "maxenergy":
            maxenergy = await redis_utils.increment_maxenergy(user.id, 500)
            extra_info['maxenergy'] = maxenergy
            
        self.session.add(user_booster_item)
        return extra_info, coins, user_booster_item
            
    
        