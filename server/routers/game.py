import json
import traceback
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from server.repositories.game import GameRepository
from server.services.game import game_service
from utils.redis_utils import redis_utils

router = APIRouter(prefix='/game')

@router.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket, initdata: str = Query(...)):
    user = await GameRepository.get_user_or_error(websocket, initdata, 'inviter')
    game_service.add_game_subscriber(user.id, websocket)
    
    await websocket.accept()
    try:
        while True:
            msg = await websocket.receive()

            if msg:
                if msg.get('type') == "websocket.disconnect":
                    raise WebSocketDisconnect()
            data = json.loads(msg.get('text'))
            eventname = data.get('eventname')
            
            if eventname == 'tap':
                clicks = data.get("clicks")
                phrase = data.get('phrase')
                try:
                    energy, coins, exp = await GameRepository.tap_handler(websocket, user, clicks, phrase, initdata)
                    await GameRepository.send_message_to_player(user.id, {"eventname":"tap", "energy": energy, "coins": coins, "exp": exp})
                except Exception as ex:
                    traceback.print_exc()
            elif eventname == 'phrase':
                phrase = await redis_utils.get_phrase(user.id)
                if not phrase:
                    phrase = await redis_utils.generate_phrase_for_user(user.id)
                await GameRepository.send_message_to_player(user.id, {
                    "eventname": "phrase", "phrase": phrase
                })
    
    except WebSocketDisconnect:
        print("websocket disconnected")
    finally:
        game_service.remove_game_subscriber(user.id)
        
