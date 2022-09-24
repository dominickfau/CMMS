from datetime import datetime
from typing import List
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas
from cmms.database import get_session
from cmms.api.extensions import login_manager


router = APIRouter(
    prefix="/equipment_failure",
    tags=['Equipment Failure']
)


@router.post("/create", response_model=schemas.EquipmentFailureOut)
async def create_equipment_failure(equipment_failure: schemas.EquipmentFailureIn, db: Session = Depends(get_session), current_user: models.User = Depends(login_manager)):
    equipment_failure_obj = db.query(models.EquipmentFailure).filter(models.EquipmentFailure.name == equipment_failure.name).first() # type: models.EquipmentFailure

    if equipment_failure_obj != None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment Failure with name: '{equipment_failure.name}' already exist.")

    new_equipment_failure = models.EquipmentFailure(name=equipment_failure.name)
    new_equipment_failure.created_by_user = current_user
    new_equipment_failure.modified_by_user = current_user
    db.add(new_equipment_failure)
    db.commit()
    db.refresh(new_equipment_failure)
    return new_equipment_failure


@router.put("/{id}", response_model=schemas.EquipmentFailureOut)
async def update_equipment_failure(id: int, equipment_failure: schemas.EquipmentFailureIn, db: Session = Depends(get_session), current_user: models.User = Depends(login_manager)):
    query = db.query(models.EquipmentFailure).filter(models.EquipmentFailure.id == id)

    updated_equipment_failure = query.first() # type: models.EquipmentFailure

    if not updated_equipment_failure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment Failure with id: {id} does not exist.")

    query.update(equipment_failure.dict(), synchronize_session=False)
    updated_equipment_failure.modified_by_user = current_user
    updated_equipment_failure.date_modified = datetime.now()
    updated_equipment_failure.remove_all_failures()
    db.commit()
    db.refresh(updated_equipment_failure)
    return updated_equipment_failure


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment_failure(id: int, db: Session = Depends(get_session), current_user: models.User = Depends(login_manager)):
    equipment_failure = db.query(models.EquipmentFailure).filter(models.EquipmentFailure.id == id).first() # type: models.EquipmentFailure

    if equipment_failure == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment Failure with id: {id} does not exist.")

    db.delete(equipment_failure)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id}", response_model=schemas.EquipmentFailureOut)
async def get_equipment_failure_by_id(id: int, db: Session = Depends(get_session)):
    equipment_failure = db.query(models.EquipmentFailure).filter(models.EquipmentFailure.id == id).first() # type: models.EquipmentFailure
    if not equipment_failure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment Failure with id: {id} does not exist.")

    return equipment_failure


@router.get("/", response_model=schemas.EquipmentFailureListOut)
async def get_cause_of_failure(name: str = "", db: Session = Depends(get_session)):
    cause_of_failures = db.query(models.EquipmentFailure).filter(models.EquipmentFailure.name.ilike("%" + name + "%")).all() # type: List[models.EquipmentFailure]
    return {"items": cause_of_failures}