from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from database import create_session
from server.repositories.task import TasksRepository
from server.services.task import TasksService

router = APIRouter(prefix='/tasks')

def get_task_service(session: AsyncSession = Depends(create_session)) -> TasksService:
    repo = TasksRepository(session)
    return TasksService(repo)


@router.get('/tasks')
async def get_tasks(service: TasksService = Depends(get_task_service), initdata: str = Header(..., alias="Authorization")):
    return await service.get_all_tasks(initdata)

@router.post('/check-task', response_model=bool)
async def check_task(task_id: int, service: TasksService = Depends(get_task_service), initdata: str = Header(..., alias="Authorization")):
    return await service.check_task(task_id, initdata)