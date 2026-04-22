from fastapi import FastAPI, Request, HTTPException, status,Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


from sqlalchemy import select
from sqlalchemy.orm import Session
from schemas import  PitchCreate, PitchResponse, RecordCreate, RecordResponse

import models
from database import get_db, Base, engine

Base.metadata.create_all(bind=engine)

from typing import Annotated

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/")
def home():
    return {"message": "Hello, World!"}

@app.post(
    "/api/users",
    response_model=PitchResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(user: PitchCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.username == user.username))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists. Please choose a different username.",
        )
    
    result = db.execute(select(models.User).where(models.User.email == user.email))
    existing_email = result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists. Please choose a different email.",
        )
    
    if user.pitch_count <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pitch count must be a positive integer.",
        )
    
    new_user = models.User(username=user.username, email=user.email, pitch_count=user.pitch_count)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@app.get("/api/users/{user_id}",response_model=PitchResponse)
def get_user(user_id:int,db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@app.post(
    "/api/records",
    response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_record(record: RecordCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == record.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if user.pitch_count < record.pitch_id and user.pitch_id > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no pitches has this pitch_id",
        )

    new_record = models.Record(
        pitch_id=record.pitch_id,
        datetime_from_st=record.datetime_from_st,
        user_id=record.user_id,
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record


@app.get("/api/records/{user_id}/{pitch_id}/{time_stamp}", response_model=RecordResponse)
def get_record(user_id: int,pitch_id:int ,time_stamp:str,db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Record).where(models.Record.user_id == user_id,
                                                    models.Record.pitch_id == pitch_id,
                                                    models.Record.date_posted.startswith(time_stamp)))
    record = result.scalars().first()
    
    if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Kayıt bulunamadı"
            )
            
    return record