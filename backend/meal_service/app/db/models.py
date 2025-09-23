from sqlmodel import SQLModel,Field,Relationship,DateTime
from typing import List, Optional
from datetime import datetime,timezone


def get_utc_now():
    return datetime.now(timezone.utc)



### MODELS
class MealModel(SQLModel, table = True):

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int

    name: str
    date: datetime = Field(default_factory=get_utc_now)

    created_at: datetime = Field(default_factory=get_utc_now, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=get_utc_now, sa_type=DateTime(timezone=True))


class RecipeModel(SQLModel, table = True):
    id: Optional[int] = Field(default=None, primary_key=True)
    meal_id: int = Field(foreign_key="mealmodel.id")

    title: str
    instructions: Optional[str] = None
    calories: Optional[float] = None

    created_at: datetime = Field(default_factory=get_utc_now, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=get_utc_now, sa_type=DateTime(timezone=True))


##SCHEMAS

class CreateMeal(SQLModel):

    
    user_id: int
    name: str
    date: Optional[datetime] = None


class UpdateMeal(SQLModel):

    name: Optional[str]
    date: Optional[datetime] = None


class GetMeal(SQLModel):

    id: int
    user_id: int
    name: str
    date: datetime
    created_at: datetime
    updated_at: datetime



class CreateRecipe(SQLModel):

    
    title:str
    instructions: Optional[str] = None
    calories: Optional[float] = None


class UpdateRecipe(SQLModel):

    title: Optional[str] = None
    instructions: Optional[str] = None
    calories: Optional[float] = None


class GetRecipe(SQLModel):

    id: int
    meal_id:int
    title: str
    instructions: str
    calories : float
    created_at: datetime
    updated_at: datetime







