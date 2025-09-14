from pickle import TRUE
from sqladmin import ModelView
from fastapi import Request
import jwt
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from database import get_session
from models import AdminUser, BoosterItem, Invoice, ShopItem, Squad, Task, User, UserBooster, UserShopItem, UserSquad, UserTask
from utils.authutils import AuthUtils

SECRET_KEY = ""

class AdminAuth(AuthenticationBackend):
    
    async def login(self, request: Request) -> bool:
        form = await request.form()
        print(form)
        username, password = form["username"], form["password"]
        async with get_session() as session:
            user_admin_query = select(AdminUser).where(AdminUser.login == username)
            user_admin_result = await session.execute(user_admin_query)
            user_admin = user_admin_result.scalar()
            if not user_admin:
                return False
            if user_admin.password != password:
                return False
            token = jwt.encode({"user_id":user_admin.id}, SECRET_KEY, algorithm="HS256")
            request.session.update({"token": token})
            return True
    
    async def logout(self, request: Request) -> bool:
        # Usually you'd want to just clear the session
        request.session.clear()
        return True
    
    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        result = False
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], verify=True)
            result = True
        finally:
            return result

authentication_backend = AdminAuth(secret_key=SECRET_KEY)



async def add_basic_admin_models(admin, models=[User, BoosterItem, UserBooster, ShopItem, UserShopItem, Squad, UserSquad, Invoice, Task, UserTask]):
    for model in models:

        class TemplView(ModelView, model=model):
            column_list = [c for c in model.__table__.columns]
            column_sortable_list = [c for c in model.__table__.columns]
            def is_visible(self, request: Request) -> bool:
                return AuthUtils.does_have_access(request)
            
            def is_accessible(self, request: Request) -> bool:
                return AuthUtils.does_have_access(request)
            
        admin.add_view(TemplView)
        