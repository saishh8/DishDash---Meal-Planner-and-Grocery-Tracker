import sqlmodel
from sqlmodel import SQLModel,Field,ForeignKey,Session
from app.helpers.config import DATABASE_URL


if DATABASE_URL == '':
    raise NotImplementedError("Database URL needs to be set")
    

engine = sqlmodel.create_engine(DATABASE_URL)

def init_db():

    print("Creating Database")
    SQLModel.metadata.create_all(engine)


def get_session():

    with Session(engine) as session:
        yield session
    