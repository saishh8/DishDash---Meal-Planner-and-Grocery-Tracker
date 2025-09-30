import httpx
from fastapi import HTTPException, status

AUTH_SERVICE_URL = "http://auth_service:8000/api/auth"  # replace with your actual auth service URL

async def verify_user(authorization: str) -> int:

    """
    Verifies the JWT token with the auth service and returns the user ID.
    Raises 401 if the token is invalid or expired.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]  # extract the token part

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{AUTH_SERVICE_URL}/me", headers={"Authorization": f"Bearer {token}"})
    
    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    
    user_data = resp.json()
    user_id = user_data.get("id")
    
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    # return user_id
    return int(user_id)  # ensure user_id is an int
    
