from typing import List, Optional
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from database import create_session
from models import Squad, UserSquad
from schemas import SquadLeadeboardResponse
from server.repositories.squad import SquadRepository
from server.services.squad import SquadService

router = APIRouter(prefix='/squad')

def get_squads_service(session: AsyncSession = Depends(create_session)) -> SquadService:
    repo = SquadRepository(session)
    return SquadService(repo)

@router.get('/my-squad', response_model=Optional[int])
async def my_squad(service: SquadService = Depends(get_squads_service), initdata: str = Header(..., alias="Authorization")):
    return await service.get_my_squad(initdata)

@router.get('/squads', response_model=List[SquadLeadeboardResponse])
async def get_squads(service: SquadService = Depends(get_squads_service), initdata: str = Header(..., alias="Authorization")):
    return await service.get_squads(initdata)
    
@router.post('/join-squad', response_model=UserSquad)
async def join_squad(squad_id:int,  service: SquadService = Depends(get_squads_service), initdata: str = Header(..., alias="Authorization")):
    return await service.join_squad(initdata, squad_id)

@router.post("/create-squad", response_model=Squad)
async def create_squad(squad_link: str, service: SquadService = Depends(get_squads_service), initdata: str = Header(..., alias="Authorization")):
    return await service.create_squad(squad_link, initdata)
