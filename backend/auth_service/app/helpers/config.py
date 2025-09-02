from decouple import config as decouple_config

DATABASE_URL = decouple_config('DATABASE_URL',default='')
SECRET_KEY=decouple_config('SECRET_KEY',default='')
ALGORITHM=decouple_config('ALGORITHM',default='')
ACCESS_TOKEN_EXPIRE_MINUTES=decouple_config('ACCESS_TOKEN_EXPIRE_MINUTES',cast=int,default=30)