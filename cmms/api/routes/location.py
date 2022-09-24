from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from cmms import models
from cmms.api import schemas
from cmms.database import get_session
from cmms.api.extensions import login_manager

router = APIRouter(
    prefix="/location",
    tags=['Location']
)


@router.post("/create", status_code=status.HTTP_201_CREATED, response_model=schemas.LocationOut)
async def create_location(location: schemas.LocationIn, db: Session = Depends(get_session)):
    location_obj = db.query(models.Location).filter(models.Location.name == location.name).first()
    if location_obj:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"A location with name: {location.name} already exists.")
    new_location = models.Location(**location.dict())
    db.add(new_location)
    db.commit()
    db.refresh(new_location)

    return new_location


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(id: int, db: Session = Depends(get_session), current_user: models.User = Depends(login_manager)):    
    location = db.query(models.Location).filter(models.Location.id == id).first() # type: models.Location

    if location == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Location with id: {id} does not exist.")

    location.delete(session=db)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/{id}', response_model=schemas.LocationOut)
async def get_location_by_id(id: int, db: Session = Depends(get_session)):
    location = db.query(models.Location).filter(models.Location.id == id).first()
    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Location with id: {id} does not exist")

    return location


@router.get('/', response_model=schemas.LocationListOut)
async def get_location(name: str="", db: Session = Depends(get_session)):
    locations = db.query(models.Location).filter(models.Location.name.ilike("%" + name + "%")).all()
    return {"items": locations}