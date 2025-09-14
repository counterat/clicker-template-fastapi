from config import ENERGY_REFILLS
from utils.scheduler import scheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin
import os
from database import engine
from fastapi.staticfiles import StaticFiles

from server.admin.admin_views import add_basic_admin_models, authentication_backend
from server.routers import booster, game, squad, task, user

app = FastAPI()

app.include_router(user.router)
app.include_router(booster.router)
app.include_router(game.router)
app.include_router(squad.router)
app.include_router(task.router)


static_dir = "static/public"
abs_static_dir = os.path.abspath(static_dir)

app.mount("/static", StaticFiles(directory=abs_static_dir), name="static")

admin = Admin(app, engine, authentication_backend=authentication_backend, templates_dir="templates")


    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

    
@app.get('/tonconnect-manifest.json')
async def return_manifest():
    js = {
    "url": "https://supermoon.meme",
    "name": "Supermoon",
    "iconUrl": "https://i.ibb.co/W2BvHWK/dc31a245-bd9e-42fb-b7c9-7b63aacca9b1.jpg"
}
    return js
    
@app.get('/config')
async def get_config():
    return {
        "ENERGY_REFILLS": ENERGY_REFILLS,
        
    }
    
@app.on_event("startup")
async def on_start():
    await add_basic_admin_models(admin)
    scheduler.start()
