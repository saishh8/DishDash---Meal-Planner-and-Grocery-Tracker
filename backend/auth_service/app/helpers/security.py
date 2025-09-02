from passlib.context import CryptContext
from datetime import datetime,timezone,timedelta
from .config import SECRET_KEY,ALGORITHM,ACCESS_TOKEN_EXPIRE_MINUTES
from jose import jwt, JWTError
secret_key = SECRET_KEY
algorithm = ALGORITHM
access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")

def hash_password(password:str) -> str:
    return pwd_context.hash(password)

def verify_password(password:str,hashed:str) -> bool:
    return pwd_context.verify(password,hashed)


def create_access_token(data:dict,expires_delta:timedelta |None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=access_token_expire_minutes))
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode,secret_key,algorithm=algorithm)


