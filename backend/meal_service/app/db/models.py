from sqlmodel import SQLModel,Field,Relationship,DateTime
from typing import List, Optional
from datetime import datetime,timezone


def get_utc_now():
    return datetime.now(timezone.utc)



### MODELS

class MealRecipeLink(SQLModel, table=True):
    meal_id: int = Field(foreign_key="mealmodel.id", primary_key=True)
    recipe_id: int = Field(foreign_key="recipemodel.id", primary_key=True)

class MealModel(SQLModel, table = True):

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int

    name: str
    date: datetime = Field(default_factory=get_utc_now)

    created_at: datetime = Field(default_factory=get_utc_now, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=get_utc_now, sa_type=DateTime(timezone=True))

    recipes: List["RecipeModel"] = Relationship(back_populates="meals",link_model=MealRecipeLink)


class RecipeModel(SQLModel, table = True):
    id: Optional[int] = Field(default=None, primary_key=True)

    title: str
    instructions: Optional[str] = None
    calories: Optional[float] = None

    created_at: datetime = Field(default_factory=get_utc_now, sa_type=DateTime(timezone=True))
    updated_at: datetime = Field(default_factory=get_utc_now, sa_type=DateTime(timezone=True))

    meals: List["MealModel"] = Relationship(back_populates="recipes",link_model=MealRecipeLink
)



##SCHEMAS

class CreateMeal(SQLModel):

    
    user_id: int
    name: str
    date: Optional[datetime] = None


class CreateRecipe(SQLModel):

    
    title: str
    instructions: Optional[str] = None
    calories: Optional[float] = None
    meal_ids: Optional[List[int]] = None  # new field for linking to meals


class UpdateMeal(SQLModel):

    name: Optional[str]
    date: Optional[datetime] = None


class UpdateRecipe(SQLModel):

    title: Optional[str] = None
    instructions: Optional[str] = None
    calories: Optional[float] = None
    meal_ids: Optional[List[int]] = None  # optional updated meal links

class GetRecipe(SQLModel):

    id: int
    title: str
    instructions: Optional[str] = None
    calories: Optional[float] = None
    meals: Optional[List[int]] = None  # list of meal IDs
    created_at: datetime
    updated_at: datetime



class GetMeal(SQLModel):

    id: int
    user_id: int
    name: str
    date: datetime
    created_at: datetime
    updated_at: datetime
    recipes: Optional[List[GetRecipe]] = None  # optional nested



