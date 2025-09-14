from fastapi import HTTPException
from bot.main import check_is_user_in_chat
from schemas import TaskResponse
from server.services.user import UserService
from utils.redis_utils import redis_utils


class TasksService(UserService):
    
    async def get_all_tasks(self, initdata:str):
        async with self.repo.session.begin():
            user = await self.repo.get_user_or_error(initdata)
            all_tasks = await self.repo.get_all_tasks()
            completed_tasks = await self.repo.get_all_tasks_completed_by_user(user.id)
            completed_tasks_ids = [c_task.task_id for c_task in completed_tasks]
            resp = []
            for task in all_tasks:
                resp.append(
                    TaskResponse(
                        task=task, is_completed=task.id in completed_tasks_ids
                    )
                )
            return resp
    
    async def check_task(self, task_id: int, initdata: str):
        async with self.repo.session.begin():
            user = await self.repo.get_user_or_error(initdata, "user_tasks")
            task  = await self.repo.get_task(task_id)
            if task.is_permanent:
                raise HTTPException(400, 'The task is permanent!')
            completed_tasks_ids = [c_task.task_id for c_task in user.user_tasks]
            if task.id in completed_tasks_ids:
                raise HTTPException(400, "The task is already completed!")
            is_completed = False
            if 't.me' in task.link:
                is_user_in_chat = await check_is_user_in_chat(task.link, user_id=user.id)
                if is_user_in_chat:
                    await self.repo.create_user_task(user.id, task_id)
                    coins = await redis_utils.increment_coins(user.id, task.reward)
                    if user.user_squad:
                        await redis_utils.increment_squad_coins(user.user_squad.squad_id, coins)
                    is_completed = True
            else:
                await self.repo.create_user_task(user.id, task_id)
                coins = await redis_utils.increment_coins(user.id, task.reward)
                is_completed = True
            return is_completed