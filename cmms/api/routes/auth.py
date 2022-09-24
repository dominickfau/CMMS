from datetime import timedelta, datetime
from typing import Optional
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login.exceptions import InvalidCredentialsException
from sqlalchemy.orm import Session
from cmms import models
from cmms.database import DBContext
from cmms.api import schemas
from cmms.api.extensions import login_manager
from cmms.config import LOGIN_TOKEN_EXPIRE_MINUTES


router = APIRouter(
    prefix="/auth",
    tags=['Users']
)

@login_manager.user_loader()
async def load_user(username: str, db: Session = None) -> Optional[models.User]:
    if db is None:
        with DBContext() as db:
            user = db.query(models.User).filter(models.User.username == username).first() # type: models.User
    else:
        user = db.query(models.User).filter(models.User.username == username).first() # type: models.User
    return user


@router.post("/token", response_model=schemas.Token)
def login(data: OAuth2PasswordRequestForm = Depends()):
    if not load_user(data):
        raise InvalidCredentialsException  # you can also use your own HTTPException
    
    with DBContext() as db:
        user = db.query(models.User).filter(models.User.username == data.username).first() # type: models.User
        db.add(user.on_login())
        db.commit()

    expires = datetime.now() + timedelta(minutes=LOGIN_TOKEN_EXPIRE_MINUTES)
    access_token = login_manager.create_access_token(data=dict(sub=data.username), expires=timedelta(minutes=LOGIN_TOKEN_EXPIRE_MINUTES))
    return schemas.Token(access_token=access_token, token_type='bearer', expire_minutes=LOGIN_TOKEN_EXPIRE_MINUTES, expires=expires)


# @router.get('/logout')
# def logout(response : Response):
#   response = RedirectResponse('/token', status_code=status.HTTP_302_FOUND)
#   response.delete_cookie(key='access-token')
#   return response