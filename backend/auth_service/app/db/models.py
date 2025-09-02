
from sqlmodel import SQLModel, Field, DateTime
from typing import Optional, List
from datetime import datetime,timezone,timedelta


def get_utc_now():

    return datetime.now(timezone.utc)


class UserModel(SQLModel,table =True):
    id: Optional[int] = Field(default=None, primary_key = True)
    email: str
    hashed_password: str

    created_at: datetime = Field(default_factory=get_utc_now,
                                sa_type=DateTime(timezone=True),
                                nullable=False)
    
    updated: datetime = Field(default_factory=get_utc_now,
                                sa_type=DateTime(timezone=True),
                                nullable=False)


class CreateUserSchema(SQLModel):
    email: str
    password:str


class UpdateSchema(SQLModel):
    email:Optional[str] = None
    password:Optional[str] = None


class GetUser(SQLModel):
    id: int
    email: str
    created_at: datetime
    updated_at: datetime


class GetAllUsers(SQLModel):
    users:List[GetUser]
    count:int





