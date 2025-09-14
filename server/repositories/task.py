from sqlmodel import select
from models import Task, UserTask
from server.repositories.user import UserRepository


class TasksRepository(UserRepository):
    
    async def get_all_tasks(self):
        tasks = await self.session.scalars(
            select(Task)
        )
        tasks = tasks.all()
        return tasks
    
    async def get_all_tasks_completed_by_user(self, user_id:int):
        completed_tasks = await self.session.scalars(
            select(UserTask).where(UserTask.user_id == user_id)
        )
        completed_tasks = completed_tasks.all()
        return completed_tasks

    async def get_task(self, task_id: int):
        task = await self.session.scalar(
            select(Task).where(Task.id == task_id)
        )
        return task

    async def create_user_task(self, user_id: int, task_id: int):
        user_task = UserTask(
            user_id=user_id,
            task_id=task_id
        )
        self.session.add(user_task)
        await self.session.flush()
        return user_task