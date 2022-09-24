from datetime import datetime
from typing import List
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, Path
from sqlalchemy.orm import Session
from .. import models, schemas
from cmms.database import get_session
from cmms.api.extensions import login_manager


router = APIRouter(
    prefix="/equipment",
    tags=['Equipment']
)


@router.post("/create", response_model=schemas.EquipmentOut)
async def create_equipment(equipment: schemas.EquipmentIn, db: Session = Depends(get_session), current_user: models.User = Depends(login_manager)):
    dict_ = equipment.dict()
    classification1_name = dict_.pop("classification1_name", None)
    classification2_name = dict_.pop("classification2_name", None)

    if classification1_name:
        classification1 = db.query(models.EquipmentClassification1.name == classification1_name).first()
        if not classification1:
            classification1 = models.EquipmentClassification1(name=classification1_name)
            db.add(classification1)
    
    if classification2_name:
        classification2 = db.query(models.EquipmentClassification2.name == classification2_name).first()
        if not classification2:
            classification2 = models.EquipmentClassification2(name=classification2_name)
            db.add(classification2)
    
    new_equipment = models.Equipment(**dict_)
    new_equipment.created_by_user = current_user
    new_equipment.set_classification1(classification1, current_user)
    new_equipment.set_classification2(classification2, current_user)
    db.add(new_equipment)
    db.commit()
    db.refresh(new_equipment)

    return new_equipment


@router.put("/{id}", response_model=schemas.EquipmentOut)
async def update_equipment(id: int, equipment: schemas.EquipmentIn, db: Session = Depends(get_session), current_user: models.User = Depends(login_manager)):
    query = db.query(models.Equipment).filter(models.Equipment.id == id)

    updated_equipment = query.first() # type: models.Equipment

    if not updated_equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment with id: {id} does not exist.")

    query.update(equipment.dict(), synchronize_session=False)
    updated_equipment.modified_by_user = current_user
    updated_equipment.date_modified = datetime.now()

    db.commit()
    db.refresh(updated_equipment)

    return updated_equipment


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment(id: int, db: Session = Depends(get_session), current_user: models.User = Depends(login_manager)):
    query = db.query(models.Equipment).filter(models.Equipment.id == id)

    equipment = query.first() # type: models.Equipment

    if equipment == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment with id: {id} does not exist.")

    query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id}", response_model=schemas.EquipmentOut)
async def get_equipment(id: int, db: Session = Depends(get_session)):
    equipment = db.query(models.Equipment).filter(models.Equipment.id == id).first() # type: models.Equipment
    if not equipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment with id: {id} does not exist.")

    return equipment


@router.get("/", response_model=schemas.EquipmentListOut)
async def get_equipment(serial_number: str = "", db: Session = Depends(get_session)):
    equipment = db.query(models.Equipment).filter(models.Equipment.serial_number.ilike("%" + serial_number + "%")).all() # type: List[models.Equipment]
    return {"items": equipment}