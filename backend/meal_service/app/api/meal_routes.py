from fastapi import APIRouter,Depends, HTTPException, Header
from sqlmodel import Session
from ..db.models import MealModel,CreateMeal,GetMeal
from ..db.session import get_session
import httpx

router = APIRouter()


AUTH_SERVICE_URL = "http://auth_service:8000/api/auth"

@router.post('/meal',response_model=GetMeal)
async def CreateMeal(meal:CreateMeal,session: Session = Depends(get_session),authorization:str = Header(...)):
    

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{AUTH_SERVICE_URL}/me", headers={"Authorization":authorization})

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail= "Invalid or expired Token")
    
    user_data = resp.json()
    user_id = user_data['id']

    new_meal = MealModel(

        user_id=user_id,
        name = meal.name,
        date=meal.date or None,
    )

    session.add(new_meal)
    session.commit()
    session.refresh(new_meal)
    return new_meal