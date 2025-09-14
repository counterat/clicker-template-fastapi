import pytest
from httpx import AsyncClient

from .context import auth_headers, client




def test_user_authorize():
    response = client.get("/user/authorize", headers=auth_headers)
    assert response.is_success == True

def test_leaderboard():
    response = client.get("/user/leaderboard", headers=auth_headers)
    assert response.is_success == True
    
def test_friends():
    response = client.get("/user/friends", headers=auth_headers)
    assert response.is_success == True
    
def test_refill_energy():
    response = client.post("/user/refill-energy", headers=auth_headers)
    assert response.is_success == True
    
def test_claim_tapped_by_tapbot():
    response = client.post("/user/claim-tapped-by-tapbot", headers=auth_headers)
    assert response.is_success == True
    
def test_tapped_by_tapbot():
    response = client.get("/user/tapped-by-tapbot", headers=auth_headers)
    assert response.is_success == True