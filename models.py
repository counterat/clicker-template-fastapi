from sqlmodel import SQLModel, Field, Relationship, table
from sqlalchemy.orm import foreign
from typing import List, Dict, Optional
from sqlalchemy import BigInteger, Column, ForeignKey, Enum
from datetime import datetime
from pydantic import model_validator
import enum
from decimal import Decimal
from uuid import uuid4


class UserPublic(SQLModel):
    id: int = Field(sa_column=Column(BigInteger, primary_key=True))
    name: str = Field(nullable=False)
    username: Optional[str] = Field(nullable=True)
    
    is_premium: bool = Field(default=False)
    invite_link: Optional[str]
    photo_url: Optional[str] = Field(nullable=True)

class UserPublicWithBalances(UserPublic):
    coins: Optional[int]
    experience: Optional[int]
    energy: Optional[int]
    coins_per_click: Optional[int]

class User(UserPublic, table=True):
    __tablename__ = "users"
    
    invited_by: Optional[int] = Field(sa_column=Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL')))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    is_deleted: bool = Field(default=False)
    
    inviter: Optional["User"] = Relationship(
        back_populates="invited_users",
        sa_relationship_kwargs={
            "remote_side": "User.id",
            "foreign_keys": "[User.invited_by]"
        }
    )
    invited_users: List["User"] = Relationship(
        back_populates="inviter",
        sa_relationship_kwargs={
            "foreign_keys": "[User.invited_by]"
        }
    )
    boosters: List["UserBooster"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={
            "foreign_keys": "[UserBooster.user_id]"
        }
    )
    shop_items: List["UserShopItem"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={
            "foreign_keys": "[UserShopItem.user_id]"
        }
    )
    user_tasks: List["UserTask"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={
            "foreign_keys": "[UserTask.user_id]"
        }
    )
    founded_squads: List["Squad"] = Relationship(
        back_populates="founder",
        sa_relationship_kwargs={
            "foreign_keys": "[Squad.founder_id]"
        }
    )
    user_squad: Optional["UserSquad"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"uselist": False}
    )
    
class BoosterItem(SQLModel, table=True):
    __tablename__ = 'booster_items'
    id: int = Field(primary_key=True)
    price: Decimal = Field()
    name: str = Field()
    
class UserBooster(SQLModel, table=True):
    __tablename__ = "user_boosters"
    id: int = Field(default=None, primary_key=True)
    booster_id: int = Field(sa_column=Column(BigInteger))
    user_id: int = Field(sa_column=Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL')))
    is_equipped: bool = Field(default=False, nullable=False)
    owner: "User" = Relationship(
        back_populates="boosters",
        sa_relationship_kwargs={
            "foreign_keys": "[UserBooster.user_id]"
        }
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
class ShopItem(SQLModel, table=True):
    __tablename__ = "shop_items"
    id: int = Field(primary_key=True)
    name: str = Field()
    price: Decimal = Field()
    coins: int = Field()
    photo_url: str = Field()
    
class UserShopItem(SQLModel, table=True):
    __tablename__ = "user_shops"
    id: int = Field(default=None, primary_key=True)
    shop_item_id: int = Field(sa_column=Column(BigInteger))
    user_id: int = Field(sa_column=Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL')))
    is_equipped: bool = Field(default=False, nullable=False)
    owner: "User" = Relationship(
        back_populates="shop_items",
        sa_relationship_kwargs={
            "foreign_keys": "[UserShopItem.user_id]"
        }
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
class Squad(SQLModel, table=True):
    __tablename__ = 'squads'
    id:int = Field(sa_column=Column(BigInteger, primary_key=True))
    founder_id: int = Field(sa_column=Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL')))
    title: str = Field()
    link_to_squad: str = Field(unique=True)
    photo_url: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    founder: Optional["User"] = Relationship(
        back_populates="founded_squads",
        sa_relationship_kwargs={
            "foreign_keys": "[Squad.founder_id]"
        }
    )
    user_squads: List["UserSquad"] = Relationship(
        back_populates='squad'
    )
    
    
class UserSquad(SQLModel, table=True):
    __tablename__ = 'user_squads'
    id:int = Field(default=None, primary_key=True)
    user_id: int = Field(sa_column=Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE")))
    squad_id: int = Field(sa_column=Column(BigInteger, ForeignKey("squads.id", ondelete="CASCADE")),)
    user: Optional[User] = Relationship(back_populates="user_squad")
    squad: Optional[Squad] = Relationship(back_populates="user_squads")


class AdminUser(SQLModel, table=True):
    __tablename__ = 'admin_users'
    id: int = Field(primary_key=True)
    login: str = Field(nullable=False)
    password: str = Field(nullable=False)
    is_superuser: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    
class ConnectionInvoiceStatus(str, enum.Enum):
    PENDING = 'PENDING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'

class Invoice(SQLModel, table=True):
    id: int = Field(primary_key=True)
    user_id: int = Field(sa_column=Column(BigInteger, ForeignKey('users.id', ondelete='SET NULL')))
    shop_item_id: int = Field(sa_column=Column(BigInteger, ForeignKey("shop_items.id", ondelete="SET NULL")))
    price: int = Field()
    status: str = Field(sa_column=Column(Enum(ConnectionInvoiceStatus), default=ConnectionInvoiceStatus.PENDING))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

class Task(SQLModel, table=True):
    __tablename__ = 'tasks'
    
    id: int = Field(primary_key=True)
    name: str = Field()
    reward: int = Field()
    link: str = Field()
    is_permanent: bool = Field()
    photo_url: str = Field()
    
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    user_tasks: List["UserTask"] = Relationship(
        back_populates='task'
    )

class UserTask(SQLModel, table=True):
    id: int = Field(primary_key=True)
    user_id: int = Field(sa_column=Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE")))
    task_id: int = Field(sa_column=Column(BigInteger, ForeignKey("tasks.id", ondelete="CASCADE")))
    user: Optional[User] = Relationship(back_populates="user_tasks")
    task: Optional[Task] = Relationship(back_populates="user_tasks")
