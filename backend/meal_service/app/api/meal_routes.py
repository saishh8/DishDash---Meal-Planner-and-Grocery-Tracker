from fastapi import APIRouter,Depends, HTTPException, Header
from typing import List
from sqlmodel import Session, select
from ..db.models import MealRecipeLink,MealModel,RecipeModel,CreateMeal,UpdateMeal,GetMeal,GetMealSummary,CreateRecipe,GetRecipe,UpdateRecipe,get_utc_now
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


#Fetch all meals for a user
@router.get('/all',response_model=List[GetMealSummary])
async def get_all_meals(authorization:str = Header(...), session: Session = Depends(get_session)):

    user_id = await verify_user(authorization)

    all_meals = session.exec(
        select(MealModel).where(MealModel.user_id == user_id)
    ).all()

    if not all_meals:
        raise HTTPException(status_code=404, detail="No meals found")
    
    # return [GetMeal.from_orm_with_recipes(meal) for meal in all_meals]
    return all_meals

#Fetch single meal for a user
@router.get('/{meal_id}',response_model=GetMeal)
async def get_meal(meal_id:int, session:Session = Depends(get_session), authorization: str = Header(...)):
    
    user_id = await verify_user(authorization)

    meal = session.exec(
        select(MealModel).where(MealModel.id == meal_id, MealModel.user_id == user_id)
    ).first()

    if not meal:
         raise HTTPException(status_code=403, detail="Meal not found or not yours")

    
    return GetMeal.from_orm_with_recipes(meal)






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
    return GetMeal.from_orm_with_recipes(meal)


# delete a meal 
@router.delete("/{meal_id}", status_code=204)
async def delete_meal(meal_id: int,session: Session = Depends(get_session),authorization: str = Header(...)):
    
    user_id = await verify_user(authorization)

    # Fetch meal and check ownership
    meal = session.get(MealModel, meal_id)
    if not meal or meal.user_id != user_id:
        raise HTTPException(status_code=404, detail="Meal not found or not yours")

    # Fetch all links for this meal
    links = session.exec(
        select(MealRecipeLink).where(MealRecipeLink.meal_id == meal_id)
    ).all()

    for link in links:
        # Delete the link
        session.delete(link)

        # Check if the recipe has any other links remaining
        remaining_links = session.exec(
            select(MealRecipeLink).where(MealRecipeLink.recipe_id == link.recipe_id)
        ).all()

        # If no other links exist, delete the recipe
        if not remaining_links:
            recipe = session.get(RecipeModel, link.recipe_id)
            if recipe:
                session.delete(recipe)

    # Finally, delete the meal itself
    session.delete(meal)

  
    session.commit()

    return None  # 204 No Content




#Recipe Creation in a meal
@router.post('/{meal_id}/recipe/create',response_model=GetRecipe)
async def create_recipe_for_meal(meal_id:int, recipe:CreateRecipe, session: Session = Depends(get_session), authorization: str = Header(...)):

    user_id = await verify_user(authorization)

    meal = session.get(MealModel, meal_id)

    if not meal or meal.user_id != user_id:
        raise HTTPException(status_code=404, detail="Meal not found or not yours")


    new_recipe = RecipeModel(

        user_id=user_id,
        title=recipe.title,
        ingredients=recipe.ingredients,
        instructions=recipe.instructions,
        calories = recipe.calories

    )

    session.add(new_recipe)
    session.commit()
    session.refresh(new_recipe)

    link = MealRecipeLink(meal_id=meal.id,recipe_id=new_recipe.id)
    session.add(link)
    session.commit()
    
    
    return GetRecipe.from_orm_with_meals(new_recipe)


#Recipe Creation for a user
@router.post('/recipe/create',response_model=GetRecipe)
async def create_recipe_for_user(recipe:CreateRecipe, session: Session = Depends(get_session), authorization: str = Header(...)):

    user_id = await verify_user(authorization)

    


    new_recipe = RecipeModel(
        
        user_id=user_id,
        title=recipe.title,
        ingredients=recipe.ingredients,
        instructions=recipe.instructions,
        calories = recipe.calories

    )

    session.add(new_recipe)
    session.commit()
    session.refresh(new_recipe)

    # link = MealRecipeLink(meal_id=meal.id,recipe_id=new_recipe.id)
    # session.add(link)
    # session.commit()
    
    
    return GetRecipe.from_orm_with_meals(new_recipe)


#link recipe to meal
@router.post('/{meal_id}/recipe/{recipe_id}/link',status_code= 201)
async def link_recipe_to_meal(meal_id:int,recipe_id:int,session:Session = Depends(get_session),authorization: str = Header(...)):

    user_id = await verify_user(authorization)

    meal = session.get(MealModel, meal_id)

    if not meal or meal.user_id != user_id:
        raise HTTPException(status_code=404, detail="Meal not found or not yours")
    
    recipe = session.get(RecipeModel,recipe_id)

    if not recipe or recipe.user_id != user_id:
        raise HTTPException(status_code=404, detail="Recipe not found or not yours")


    # Prevent duplicate linking
    existing_link = session.exec(
        select(MealRecipeLink).where(

            MealRecipeLink.meal_id == meal_id,
            MealRecipeLink.recipe_id == recipe_id
        )
    ).first()

    if existing_link:
        raise HTTPException(status_code=400, detail="Recipe already linked to this meal")

    # Create link
    link = MealRecipeLink(meal_id=meal_id, recipe_id=recipe_id)
    session.add(link)
    session.commit()

    return {"message": f"Recipe {recipe_id} linked to meal {meal_id}"}



#unlink recipe to meal
@router.delete("/{meal_id}/recipe/{recipe_id}/unlink", status_code=204)
async def unlink_recipe_from_meal(meal_id: int, recipe_id: int, session: Session = Depends(get_session), authorization: str = Header(...)):
    user_id = await verify_user(authorization)

    meal = session.get(MealModel, meal_id)
    if not meal or meal.user_id != user_id:
        raise HTTPException(status_code=404, detail="Meal not found or not yours")

    recipe = session.get(RecipeModel, recipe_id)
    if not recipe or recipe.user_id != user_id:
        raise HTTPException(status_code=404, detail="Recipe not found or not yours")

    # Remove link if exists
    link = session.exec(
        select(MealRecipeLink).where(
            MealRecipeLink.meal_id == meal_id,
            MealRecipeLink.recipe_id == recipe_id
        )
    ).first()

    if not link:
        raise HTTPException(status_code=404, detail="Recipe not linked to this meal")

    session.delete(link)
    session.commit()

    return {"message": f"Recipe {recipe_id} unlinked from meal {meal_id}"}



    



# Fetch a recipe for a meal (many to many)
@router.get("/{meal_id}/recipe/{recipe_id}", response_model=GetRecipe)
async def get_recipe(meal_id:int, recipe_id: int,session: Session = Depends(get_session),authorization: str = Header(...)):

   
    user_id = await verify_user(authorization)

    recipe = session.get(RecipeModel, recipe_id)
    
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    
    if not any(meal.id == meal_id and meal.user_id == user_id for meal in recipe.meals):
        raise HTTPException(status_code=404, detail= "Recipe not found or not yours")

    return GetRecipe.from_orm_with_meals(recipe)


# Fetch all recipes for a user
@router.get("/user/recipes", response_model=List[GetRecipe])
async def get_all_recipes(session:Session = Depends(get_session), authorization: str = Header(...)):

    user_id = await verify_user(authorization)

    recipes = session.exec(
        select(RecipeModel)
        .join(MealRecipeLink, MealRecipeLink.recipe_id == RecipeModel.id)
        .join(MealModel, MealRecipeLink.meal_id == MealModel.id)
        .where(MealModel.user_id == user_id).distinct(RecipeModel.id)
    ).all()
    
    return [GetRecipe.from_orm_with_meals(recipe) for recipe in recipes]


# Fetch all recipes for a meal
@router.get('/{meal_id}/recipes',response_model=List[GetRecipe])
async def get_meal_recipes(meal_id: int, session: Session = Depends(get_session), authorization: str = Header(...)):

    user_id = await verify_user(authorization)

    meal = session.get(MealModel, meal_id)
    if not meal or meal.user_id != user_id:
        raise HTTPException(status_code=404, detail="Meal not found or not yours")

    return [GetRecipe.from_orm_with_meals(recipe) for recipe in meal.recipes]


# Update a recipe directly for a user (no meal_id required)
@router.patch("/user/recipe/{recipe_id}", response_model=GetRecipe)
async def update_user_recipe(recipe_id: int,data: UpdateRecipe,session: Session = Depends(get_session),authorization: str = Header(...)):
    
   
    user_id = await verify_user(authorization)

  
    recipe = session.get(RecipeModel, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    
    if recipe.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this recipe")

    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(recipe, field, value)

   
    recipe.updated_at = get_utc_now()

  
    session.add(recipe)
    session.commit()
    session.refresh(recipe)

    return GetRecipe.from_orm_with_meals(recipe)


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
    return GetRecipe.from_orm_with_meals(recipe)




# Delete a recipe from user's library
@router.delete("/user/recipe/{recipe_id}", status_code=204)
async def delete_user_recipe(recipe_id: int,session: Session = Depends(get_session),authorization: str = Header(...),):

   
    user_id = await verify_user(authorization)

   
    recipe = session.get(RecipeModel, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

   
    if recipe.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this recipe")


    links = session.exec(
        select(MealRecipeLink).where(MealRecipeLink.recipe_id == recipe.id)
    ).all()
    for link in links:
        session.delete(link)

   
    session.delete(recipe)
    session.commit()

   
    return None


# Delete recipe from a meal (and recipe entirely if no more links)
@router.delete('/{meal_id}/recipe/{recipe_id}', status_code=204)
async def delete_recipe(meal_id: int, recipe_id: int, session: Session = Depends(get_session), authorization: str = Header(...)):

    user_id = await verify_user(authorization)

   
    recipe = session.get(RecipeModel, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Check if the recipe is linked to the meal and owned by the user
    link = session.exec(
        select(MealRecipeLink)
        .join(MealModel, MealRecipeLink.meal_id == MealModel.id)
        .where(MealRecipeLink.recipe_id == recipe_id, MealRecipeLink.meal_id == meal_id, MealModel.user_id == user_id)
    ).first()

    if not link:
        raise HTTPException(status_code=404, detail="Recipe not linked to this meal or not yours")

   
    session.delete(link)
    session.commit() 

    # Check if any remaining links exist for this recipe
    remaining_links = session.exec(
        select(MealRecipeLink).where(MealRecipeLink.recipe_id == recipe_id)
    ).first()

    if not remaining_links:
        session.delete(recipe)
        session.commit()  

    return None



