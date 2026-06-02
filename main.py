from fastapi import FastAPI, Request, HTTPException, status,Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


from sqlalchemy import select
from sqlalchemy.orm import Session
from schemas import  PitchCreate, PitchResponse, RecordCreate, RecordResponse,LoginRequest, TokenResponse

import models
from database import get_db, Base, engine

from datetime import datetime

Base.metadata.create_all(bind=engine)

from typing import Annotated

from passlib.context import CryptContext  

from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/swagger-login")

def get_current_user_from_token(token: str = Depends(oauth2_scheme)):

    if "secret_abc123" not in token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçersiz veya eksik Token! Giriş yapmalısınız.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

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
    
    hashed_pwd = pwd_context.hash(user.password)

    new_user = models.User(username=user.username, email=user.email, pitch_count=user.pitch_count,hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@app.post("/api/auth/login", response_model=TokenResponse)
def login(login_data: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    # 1. Kullanıcıyı DB'de ara
    result = db.execute(select(models.User).where(models.User.username == login_data.username))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hatalı kullanıcı adı veya şifre."
        )
    
    # 2. Passlib ile Şifre Doğrulama (Kritik Satır)
    # verify() fonksiyonu: (gelen_düz_şifre, veritabanındaki_hashli_şifre) alır
    is_password_correct = pwd_context.verify(login_data.password, user.hashed_password)
    
    if not is_password_correct:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hatalı kullanıcı adı veya şifre."
        )
    
    # 3. Giriş başarılı! Geçici bir token dönüyoruz
    generated_token = f"token_user_id_{user.id}_secret_abc123"
    
    return {
        "access_token": generated_token,
        "token_type": "bearer"
    }

@app.post("/api/auth/swagger-login", include_in_schema=False) 
def swagger_login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Annotated[Session, Depends(get_db)]):
    # Formdan gelen veriyi alıp yukarıdaki JSON bekleyen fonksiyonuna pasla
    from schemas import LoginRequest
    json_data = LoginRequest(username=form_data.username, password=form_data.password)
    return login(login_data=json_data, db=db)


@app.get("/api/users/{user_id}",response_model=PitchResponse)
def get_user(user_id:int,db: Annotated[Session, Depends(get_db)],current_token: str = Depends(get_current_user_from_token)):
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


@app.get("/api/records/{user_id}/{pitch_id}", response_model=list[RecordResponse])
def get_record(user_id: int,pitch_id:int ,time_stamp:str,db: Annotated[Session, Depends(get_db)],current_token: str = Depends(get_current_user_from_token)):
    result = db.execute(select(models.Record).where(models.Record.user_id == user_id,
                                                    models.Record.pitch_id == pitch_id,
                                                    models.Record.datetime_from_st.startswith(time_stamp)))
    record = result.scalars().all()
    
    if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Kayıt bulunamadı"
            )
    
    video_base_url = "http://127.0.0.1:8085/matches"
    for r in record:
        organized_record = datetime.strptime(r.datetime_from_st, "%d/%m/%y %H:%M:%S")
        video_name = organized_record.strftime("%d%m%y_%H") + ".mp4" # Örn: 250426_12.mp4
        
        r.video_url = f"{video_base_url}/user_{r.user_id}/pitch_{r.pitch_id}/{video_name}"
            
    return record