from typing import Dict

from fastapi import WebSocket
from sqlmodel import SQLModel


class GameService:
    
    def __init__(self) -> None:
        self._game_subscribers: Dict[int, WebSocket] = {}
    
    @property
    def game_subscribers(self) -> Dict[int, WebSocket]:
        return self._game_subscribers

    def add_game_subscriber(self, game_id: int, websocket: WebSocket):
        self._game_subscribers[game_id] = websocket

    def remove_game_subscriber(self, game_id: int):
        if game_id in self._game_subscribers:
            del self._game_subscribers[game_id]
            
    async def send_message_to_player(self, user_id: int, data:Dict):
        try:
            if user_id in self._game_subscribers:
                await self._game_subscribers[user_id].send_json(data)
        except Exception as ex:
            print(ex)
    
    def convert_to_schema(schema_cls: type[SQLModel], model_obj: SQLModel) -> SQLModel:
        return schema_cls.model_validate(model_obj)        
    
game_service = GameService()