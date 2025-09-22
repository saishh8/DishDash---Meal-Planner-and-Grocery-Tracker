from fastapi import APIRouter, HTTPException ,Depends, status
from fastapi.security import OAuth2PasswordBearer
from ..db.models import UserModel,GetUser,GetAllUsers,CreateUserSchema,UpdateSchema
from ..db.session import get_session
from sqlmodel import Session, select
from ..helpers.security import hash_password,verify_password,create_access_token,decode_access_token
from jose import jwt, JWTError


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")  # points to your login route


@router.post('/register',response_model = GetUser)
async def register(user:CreateUserSchema,session: Session = Depends(get_session)):

    existing_user = session.exec(
        select(UserModel).where(UserModel.email == user.email)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400,detail="Email already registered")
    

    user = UserModel(
        email = user.email,
        hashed_password = hash_password(user.password)
    )

    session.add(user)
    session.commit()
    session.refresh(user)
    return user




@router.post('/login')
async def login(user:CreateUserSchema, session:Session = Depends(get_session)):

    db_user = session.exec(
        select(UserModel).where(UserModel.email == user.email)
    ).first()

    if not user or not verify_password(user.password,db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")


    access_token = create_access_token(data={"sub":str(db_user.id)})
    return {"access_token":access_token,"token_type":"bearer"}



def get_current_user(token:str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> UserModel:


    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id: str = payload.get("sub")

    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = session.get(UserModel, int(user_id))
    if user is None:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user



@router.get('/me',response_model=GetUser)
async def fetch_user(user:UserModel = Depends(get_current_user)):
    return user






