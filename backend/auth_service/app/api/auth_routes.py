from fastapi import APIRouter, HTTPException ,Depends
from ..db.models import UserModel,GetUser,GetAllUsers,CreateUserSchema,UpdateSchema
from ..db.session import Session,get_session
from sqlmodel import Session, select
from ..helpers.security import hash_password,verify_password,create_access_token

router = APIRouter()


@router.post('/register',response_model = GetUser)
async def register(user:CreateUserSchema,session: Session = Depends(get_session)):

    existing_user = session.exec(
        select(UserModel).where(UserModel.email == user.email)
    ).first()

    if existing_user:
        raise HTTPException(status_code=400,detail="Email already registered")
    

    user = UserModel(
        email = user.email,
        password = hash_password(user.password)
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

    if not user or verify_password(user.password,db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")


    access_token = create_access_token(data={"sub":str(db_user.id)})
    return {"access_token":access_token,"token_type":"bearer"}






