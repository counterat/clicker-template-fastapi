import hashlib
import hmac
from urllib.parse import unquote

from fastapi import Request
from config import test_user, ENV
import json
import jwt
from database import get_sync_session

from models import AdminUser


class AuthUtils:
    
    @staticmethod
    def validate_init_data(init_data: str, bot_token: str):
        try:
            print(init_data)
            if  ENV == 'DEV':
                return True, test_user(init_data)
                
            
            vals = {k: unquote(v) for k, v in [s.split('=', 1) for s in init_data.split('&')]}
            data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted(vals.items()) if k != 'hash')

            secret_key = hmac.new("WebAppData".encode(), bot_token.encode(), hashlib.sha256).digest()
            h = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256)
            print(vals)
            return h.hexdigest() == vals['hash'], json.loads(vals['user'])
        except:
            return None, None
        
    def does_have_access(request:Request, return_admin=False):
        from server.admin.admin_views import SECRET_KEY
        token = request.session.get("token")
        if not token:
            return False
        with get_sync_session() as session:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], verify=True)
            user_id = payload.get("user_id")
            
            admin_user = session.query(AdminUser).filter(AdminUser.id == user_id).first()
            
            if return_admin:
                return user_id, admin_user
        
            if admin_user.is_superuser:
                return True
            return False
            