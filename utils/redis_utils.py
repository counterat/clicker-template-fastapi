from datetime import datetime
import secrets
import time
import traceback
from typing import Dict
from redis.asyncio import Redis
from config import REDIS_URL
import statistics

r = Redis.from_url(REDIS_URL, decode_responses=True)

class RedisUtils:
    
    def __init__(self) -> None:
        pass
    
    async def get_all_energy_rows(self):
        keys = await r.keys("energy:*")
        result = {}
        for key in keys:
            
            value = await r.get(key)
            key = key.replace("energy:", "")
            result[int(key)] = int(value) if value is not None else 0
        return result
    
    async def incr_squad_coins(self, squad_id: int, coins: int = 0):
        coins = await r.zincrby("squad_coins", coins, squad_id)
        return coins
    
    async def get_squad_coins(self, squad_id: int):
        coins = await r.zscore("squad_coins", squad_id)
        return int(coins) if coins else 0

    async def increment_squad_coins(self, squad_id: int, batch: int):
        squad_coins = await r.zincrby("squad_coins", batch, squad_id)
        return int(squad_coins)
    
    async def get_all_users_invited_by(self):
        keys = await r.keys("invited_by:*")
        result = {}
        for key in keys:
            value = await r.get(key)
            result[int(key)] = int(value) if value else 0
        return result
    
    async def set_in_squad(self, user_id:int, squad_id:int):
        await r.set(f"in_squad:{user_id}", squad_id)
        
    async def get_in_squad(self, user_id:int):
        value = await r.get(f'in_squad:{user_id}')
        if value:
            return int(value)
        return None
    
    async def init_user_state(self, user_id: int, coins: int = 0, experience: int = 0, energy: int = 1000, invited_by: int = None):
        await r.setnx(f"coins:{user_id}", coins)
        await r.setnx(f"experience:{user_id}", experience)
        await r.setnx(f"energy:{user_id}", energy)
        await r.setnx(f'coins_per_click:{user_id}', 1)
        await r.setnx(f"maxenergy:{user_id}", energy)
        coins_per_click, maxenergy = 1, energy
        tapped_by_tapbot = await r.setnx(f"tapped_by_tapbot:{user_id}", 0)
        if invited_by:
            invited_by = await r.setnx(f"invited_by:{user_id}", invited_by)
        return coins, experience, energy, coins_per_click, maxenergy
    
    async def get_user_state(self, user_id: int):
        coins = await r.get(f"coins:{user_id}")
        experience = await r.get(f"experience:{user_id}")
        energy = await r.get(f"energy:{user_id}")
        coins_per_click = await r.get(f"coins_per_click:{user_id}")
        maxenergy = await r.get(f"maxenergy:{user_id}")
        return coins, experience, energy, coins_per_click, maxenergy
    
    async def get_clicked_today(self, user_id: int):
        key = f"clicked_today:{user_id}"
        clicked_today = await r.get(key)
        return clicked_today
    
    async def increment_clicked_today(self, user_id: int, batch: int):
        key = f"clicked_today:{user_id}"

        # INCRBY автоматически создаст ключ, если его нет
        is_new = not await r.exists(key)

        clicked_today = await r.incrby(key, batch)

        if is_new:
            await r.expire(key, 86400)  # 24 часа в секундах

        return clicked_today
    
    async def increment_clicked_for_friend(self, user_id:int, batch: int):
        key = f'clicked_for_friend:{user_id}'
        clicked_for_friend = await r.incrby(key, batch)
        return clicked_for_friend
    
    async def get_refills_made(self, user_id:int):
        key = f"refills_made:{user_id}"
        value = await r.get(key)
        if not value:
            return 0
        return int(value)
    
    
    async def change_refills_made(self, user_id:int):
        key = f"refills_made:{user_id}"
        value = await r.get(key)
        if not value:
            value = await r.setnx(key, 1)
            await r.expire(key, 24*60*60)
        value = int(value)
        if value < 20:
            value = await r.incr(key, 1)
            return value
        
    async def increment_tapped_by_tapbot(self, user_id: int, batch: int):
        return await r.incrby(f"tapped_by_tapbot:{user_id}", batch)
    
    async def decrement_tapped_by_tapbot(self, user_id: int, batch: int):
        return await r.decrby(f"tapped_by_tapbot:{user_id}", batch)
    
    async def get_tapped_by_tapbot(self, user_id: int):
        tapped_by_tapbot = int(await r.get(f"tapped_by_tapbot:{user_id}"))
        return tapped_by_tapbot
    
    async def increment_experience(self, user_id: int, batch: int):
        return await r.incrby(f"experience:{user_id}", batch)
    
    async def increment_coins(self, user_id: int, batch: int) -> int:
        print("batch", batch)
        await r.zincrby("coins", int(batch), user_id)
        if batch > 0:
            return await r.incrby(f"coins:{user_id}", batch)
        return await r.decrby(f"coins:{user_id}", abs(int(batch)))
    
    async def decrement_energy(self, user_id: int, batch: int) -> int:
        return await r.decrby(f"energy:{user_id}", batch)

    async def increment_energy(self, user_id: int, batch: int, is_set:bool=False) -> int:
        if not is_set:  
            return await r.incrby(f"energy:{user_id}", batch)
        return await r.set(f"energy:{user_id}", batch)
    
    async def get_maxenergy(self, user_id:int):
        maxenergy = await r.get(f"maxenergy:{user_id}")
        return int(maxenergy)
        
    async def decrement_maxenergy(self, user_id: int, batch: int) -> int:
        return await r.decrby(f"maxenergy:{user_id}", batch)

    async def increment_maxenergy(self, user_id: int, batch: int) -> int:
        return await r.incrby(f"maxenergy:{user_id}", batch)

    async def get_user_coins(self, user_id:int):
        return  int (await r.get(f'coins:{user_id}'))
    
    async def increment_coins_per_click(self, user_id: int, batch: int):
        return int( await r.incrby(f"coins_per_click:{user_id}", batch))
    
    async def decrement_coins_per_click(self, user_id: int, batch: int):
        return int(await r.decrby(f"coins_per_click:{user_id}", batch))
    
    async def get_coins_per_click(self, user_id:int):
        coins_per_click = int(await r.get(f"coins_per_click:{user_id}"))
        return coins_per_click
    
    async def change_state_by_clicks(self, user_id: int, batch: int):
        coins_per_click = int(await r.get(f"coins_per_click:{user_id}"))
        coins = coins_per_click * batch
        energy = int(await r.get(f'energy:{user_id}'))
        is_rate_limited = await self.is_rate_limited(user_id)
        print(energy, coins, is_rate_limited, "energy, coins, is_rate_limited")
        if energy >= coins and not is_rate_limited:
            energy = await self.decrement_energy(user_id, coins)
            coins_user = await self.increment_coins(user_id, coins)
            exp = await self.increment_experience(user_id, coins)
            await self.add_click_timestamp(user_id, coins_per_click)
            in_squad = await self.get_in_squad(user_id)
            if in_squad:
                await self.increment_squad_coins(in_squad, coins)
            return energy, coins_user, exp, coins_per_click
        raise Exception
    
    async def get_users_leaderboard(self):
        leaderboard = await r.zrevrange("coins", 0, -1, withscores=True)
        return leaderboard
    
    async def generate_phrase_for_user(self, user_id: int) -> str:
        timestamp = int(datetime.utcnow().timestamp())
        salt = secrets.token_hex(4)
        phrase = f"{salt}"
        key = f"click_phrase:{user_id}"
        await r.set(key, phrase)
        return phrase

    async def get_phrase(self, user_id: int):
        resp = await r.get(f"click_phrase:{user_id}")
        return resp

    async def is_valid_phrase(self, user_id:int, phrase: str):
        resp = await self.get_phrase(user_id)
        return resp == phrase
        
    async def is_rate_limited(self,user_id: int, max_rate: int = 61) -> bool:
        now_sec = int(time.time())
        key = f"click_rate:{user_id}"
        count = await r.incr(key)
        await r.expire(key, 60)
        return count > max_rate

    async def create_tapbot(self, user_id:int, minutes_to_work:int=6*60):
        key = f"tapbot:{user_id}"
        await r.setnx(key, 0)
        await r.expire(key, minutes_to_work*60)
        
        
    async def get_tapbot(self, user_id:int):
        key = f"tapbot:{user_id}"
        coins_tapped = int(await r.get(key))
        return coins_tapped
    
    async def increment_tapbot(self, user_id:int, batch:int):
        key = f"tapbot:{user_id}"
        coins_tapped = await r.incrby(key, batch)
        return coins_tapped
    
        
    async def get_all_tapbots(self):
        keys = await r.keys("tapbot:*")
        result = {}

        for key in keys:
            value = await r.get(key)
            result[int(key)] = int(value) if value else 0

        return result        
    
    # Получить топ сквадов по коинам (по убыванию)
    async def get_sorted_squads_by_coins(self, limit: int = 100) -> Dict[int, int]:
        # ZREVRANGE: от большего к меньшему, WITHSCORES=True — вернуть также количество коинов
        top_squads = await r.zrevrange("squad_coins", 0, limit - 1, withscores=True)
        return {int(squad_id): int(coins) for squad_id, coins in top_squads}

    
    async def decrement_coins(self, user_id: int, batch: int) -> int:
        
        coins = int(await r.get(f"coins:{user_id}"))
        if coins >= batch:
            await r.zincrby("coins", -batch, user_id)
            new_coins = await self.increment_coins(user_id, -batch)    
            return new_coins
        return coins
    
    async def add_click_timestamp(self, user_id: int, clicks: int):
        timestamp = datetime.utcnow().timestamp()
        member = f"{timestamp}:{clicks}"
        await r.zadd(f"click_history:{user_id}", {member: timestamp})
        await r.expire(f"click_history:{user_id}", 60)

    async def is_human_clicking(self, user_id: int, window: int = 10) -> bool:
        raw_entries = await r.zrange(f"click_history:{user_id}", -window, -1)
        timestamps = []
        clicks = []

        for entry in raw_entries:
            try:
                ts_str, clicks_str = entry.split(":")
                timestamps.append(float(ts_str))
                clicks.append(int(clicks_str))
            except ValueError:
                traceback.print_exc()
                continue

        if len(timestamps) < 3:
            return True  # недостаточно данных для оценки

        intervals = [t2 - t1 for t1, t2 in zip(timestamps[:-1], timestamps[1:])]
        avg_clicks = sum(clicks) / len(clicks)

        try:
            variance = statistics.variance(intervals)
        except statistics.StatisticsError:
            traceback.print_exc()
            return True  # на всякий случай

        too_uniform = False #variance < 0.005     # почти одинаковые интервалы
        too_clicky = avg_clicks > 25       # много кликов за батч

        if too_uniform:
            print(f"[BOT] suspiciously stable intervals: {intervals} → variance={variance:.5f}")
        if too_clicky:
            print(f"[BOT] avg_clicks too high: {avg_clicks:.2f}")

        return not (too_uniform or too_clicky)


redis_utils = RedisUtils()