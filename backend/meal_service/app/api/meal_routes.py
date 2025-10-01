from fastapi import APIRouter,Depends, HTTPException, Header
from typing import List
from sqlmodel import Session, select
from ..db.models import MealRecipeLink,MealModel,RecipeModel,CreateMeal,UpdateMeal,GetMeal,CreateRecipe,GetRecipe,UpdateRecipe,get_utc_now
from ..db.session import get_session
import httpx
from ..helpers.security import verify_user

router = APIRouter()



# AUTH_SERVICE_URL = "http://auth_service:8000/api/auth"



#Meal Creation
@router.post('/create',response_model=GetMeal)
async def create_meal(meal:CreateMeal,session: Session = Depends(get_session),authorization:str = Header(...)):
    
    # async with httpx.AsyncClient() as client:
    #     resp = await client.get(f"{AUTH_SERVICE_URL}/me", headers={"Authorization":authorization})

    # if resp.status_code != 200:
    #     raise HTTPException(status_code=401, detail= "Invalid or expired Token")
    
    # user_data = resp.json()
    # user_id = user_data['id']
  

    user_id = await verify_user(authorization)

    new_meal = MealModel(

        user_id=user_id,
        name = meal.name,
        date=meal.date or None,
    )

    session.add(new_meal)
    session.commit()
    session.refresh(new_meal)
    return new_meal


#Fetch single meal for a user
@router.get('/{meal_id}',response_model=GetMeal)
async def get_meal(meal_id:int, session:Session = Depends(get_session), authorization: str = Header(...)):
    
    user_id = await verify_user(authorization)

    meal = session.exec(
        select(MealModel).where(MealModel.meal_id == meal_id, MealModel.user_id == user_id)
    ).first()

    if not meal:
         raise HTTPException(status_code=403, detail="Meal not found or not yours")

    
    return meal


#Fetch all meals for a user
@router.get('/all',response_model=List[GetMeal])
async def get_all_meals(authorization:str = Header(...), session: Session = Depends(get_session)):

    user_id = await verify_user(authorization)

    all_meals = session.exec(
        select(MealModel).where(MealModel.user_id == user_id).all()
    )

    if not all_meals:
        raise HTTPException(status_code=404, detail="No meals found")
    
    return all_meals



#Update meal details for a user
@router.patch('/{meal_id}',response_model=GetMeal)
async def update_meal(meal_id:int, meal_data : UpdateMeal, session: Session = Depends(get_session),authorization:str = Header(...)):

    user_id = await verify_user(authorization)

    # Fetch and check ownership
    meal = session.get(MealModel, meal_id)
    if not meal or meal.user_id != user_id:
        raise HTTPException(status_code=404, detail="Meal not found or not yours")

    # Update fields
    for key, value in meal_data.model_dump(exclude_unset=True).items():
        setattr(meal, key, value)

    meal.updated_at = get_utc_now()
    session.add(meal)
    session.commit()
    session.refresh(meal)
    return meal



@router.delete("/{meal_id}", status_code=204)
async def delete_meal(meal_id: int,session: Session = Depends(get_session),authorization: str = Header(...)):
    
    user_id = await verify_user(authorization)

    # Fetch meal and check ownership
    meal = session.get(MealModel, meal_id)
    if not meal or meal.user_id != user_id:
        raise HTTPException(status_code=404, detail="Meal not found or not yours")

    #Optional: delete associated recipes
    recipes = session.exec(select(RecipeModel).where(RecipeModel.meal_id == meal_id)).all()
    for r in recipes:
        session.delete(r)

    #Delete the meal
    session.delete(meal)
    session.commit()

    return None  # 204 No Content




#Recipe Creation
@router.post('/{meal_id}/create',response_model=GetRecipe)
async def create_recipe(meal_id:int, recipe:CreateRecipe, session: Session = Depends(get_session), authorization: str = Header(...)):

    user_id = await verify_user(authorization)

    meal = session.get(MealModel, meal_id)

    if not meal or meal.user_id != user_id:
        raise HTTPException(status_code=404, detail="Meal not found or not yours")


    new_recipe = RecipeModel(

        title=recipe.title,
        instructions=recipe.instructions,
        calories = recipe.calories

    )

    session.add(new_recipe)
    session.commit()
    session.refresh(new_recipe)

    link = MealRecipeLink(meal_id=meal.id,recipe_id=new_recipe.id)
    session.add(link)
    session.commit()
    
    
    return new_recipe




# Fetch a recipe for a meal (many to many)
@router.get("/{meal_id}/recipe/{recipe_id}", response_model=GetRecipe)
async def get_recipe(meal_id:int, recipe_id: int,session: Session = Depends(get_session),authorization: str = Header(...)):

   
    user_id = await verify_user(authorization)

    recipe = session.get(RecipeModel, recipe_id)
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    if not any(meal.id == meal_id and meal.user_id == user_id for meal in recipe.meals):
        raise HTTPException(status_code=404, detail= "Recipe not found or not yours")

    return recipe

# Fetch all recipes for a meal
@router.get('/{meal_id}/recipes',response_model=List[GetRecipe])
async def get_meal_recipes(meal_id: int, session: Session = Depends(get_session), authorization: str = Header(...)):

    user_id = await verify_user(authorization)

    meal = session.get(MealModel, meal_id)
    if not meal or meal.user_id != user_id:
        raise HTTPException(status_code=404, detail="Meal not found or not yours")

    return meal.recipes


# Fetch all recipes for a user
@router.get("/recipes", response_model=List[GetRecipe])
async def get_all_recipes(session:Session = Depends(get_session), authorization: str = Header(...)):

    user_id = await verify_user(authorization)

    recipes = session.exec(
        select(RecipeModel)
        .join(MealRecipeLink, MealRecipeLink.recipe_id == RecipeModel.id)
        .join(MealModel, MealRecipeLink.meal_id == MealModel.id)
        .where(MealModel.user_id == user_id)
    ).all()
    
    return recipes


#Update recipe for a meal belonging to a user
@router.patch("/{meal_id}/recipe/{recipe_id}", response_model=GetRecipe)
async def update_recipe(meal_id: int, recipe_id: int, data: UpdateRecipe, session: Session = Depends(get_session), authorization:str = Header(...)):


    user_id = await verify_user(authorization)


    recipe = session.get(RecipeModel, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    if not any(meal.id == meal_id and meal.user_id == user_id for meal in recipe.meals):
        raise HTTPException(status_code=404, detail="Recipe not linked to this meal or not yours")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(recipe, field, value)

    recipe.updated_at = get_utc_now()
    session.add(recipe)
    session.commit()
    session.refresh(recipe)
    return recipe


#Delete recipe
@router.delete('/{meal_id}/recipe/{recipe_id}', status_code=204)
async def delete_recipe(meal_id: int, recipe_id: int,session: Session = Depends(get_session),authorization: str = Header(...)):

    user_id = await verify_user(authorization)

    recipe = session.get(RecipeModel,recipe_id)

    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    if not any(meal.id == meal_id and meal.user_id == user_id for meal in recipe.meals):
        raise HTTPException(status_code=404, detail="Recipe not linked to this meal or not yours")
    
    #remove link to this meal first
    link = session.exec(
        select(MealRecipeLink).where(MealRecipeLink.recipe_id==recipe.id, MealRecipeLink.meal_id==meal_id)
    ).first()
    if link:
        session.delete(link)

    #delete recipe entirely if no more links
    if not recipe.meals or len(recipe.meals) == 0:
        session.delete(recipe)

    session.commit()
    return None

