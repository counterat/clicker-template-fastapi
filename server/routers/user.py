from typing import List
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from database import create_session
from models import UserPublic, UserPublicWithBalances
from schemas import BoostersResponse, ClaimCoinsForTapbot, GetFriendsResponse, UserPublicExtended
from server.repositories.user import UserRepository
from server.services.user import UserService

router = APIRouter(prefix='/user')

def get_user_service(session: AsyncSession = Depends(create_session)) -> UserService:
    repo = UserRepository(session)
    return UserService(repo)

@router.get('/authorize', response_model=UserPublicExtended)
async def authorize(service: UserService = Depends(get_user_service), initdata: str = Header(..., alias="Authorization")):
    return await service.authorize(initdata)

@router.get('/tapped-by-tapbot', response_model=int)
async def tapped_by_tapbot(service: UserService = Depends(get_user_service), initdata: str = Header(..., alias="Authorization")):
    return await service.tapped_by_tapbot(initdata)

@router.post("/claim-tapped-by-tapbot", response_model=ClaimCoinsForTapbot)
async def claim_tapped_by_tapbot(service: UserService = Depends(get_user_service), initdata: str = Header(..., alias="Authorization")):
    return await service.claim_tapped_by_tapbot(initdata)

@router.post("/refill-energy")
async def refill_energy(service: UserService = Depends(get_user_service), initdata: str = Header(..., alias="Authorization")):
    return await service.refill_energy(initdata)

@router.get('/friends', response_model=List[GetFriendsResponse])
async def get_friends(service: UserService = Depends(get_user_service), initdata: str = Header(..., alias="Authorization")):
    return await service.get_friends(initdata)

@router.get("/leaderboard", response_model=List[GetFriendsResponse])
async def get_leaderboard(service: UserService = Depends(get_user_service), initdata: str = Header(..., alias="Authorization")):
    return await service.get_leaderboard(initdata)

