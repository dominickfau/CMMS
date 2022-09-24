from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from cmms import models
from cmms.api import schemas
from cmms.database import get_session

router = APIRouter(
    prefix="/users",
    tags=['Users']
)


@router.post("/create", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_session)):
    current_user = db.query(models.User).filter(models.User.username == user.username).first()
    if current_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"A user with username: {user.username} already exists.")
    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get('/{id}', response_model=schemas.UserOut)
async def get_user_by_id(id: int, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id: {id} does not exist")

    return user


@router.get('/', response_model=schemas.UserListOut)
async def get_user(username: str="", db: Session = Depends(get_session)):
    users = db.query(models.User).filter(models.User.username.ilike("%" + username + "%")).all()
    return {"items": users}