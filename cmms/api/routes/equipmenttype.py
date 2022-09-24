from datetime import datetime
from typing import List
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas
from cmms.database import get_session
from cmms.api.extensions import login_manager


router = APIRouter(
    prefix="/equipment_type",
    tags=['Equipment Type']
)


@router.post("/create", response_model=schemas.EquipmentTypeOut)
async def create_equipment_type(equipment_type: schemas.EquipmentTypeIn, db: Session = Depends(get_session), current_user: models.User = Depends(login_manager)):
    equipment_type_obj = db.query(models.EquipmentType).filter(models.EquipmentType.name == equipment_type.name).first() # type: models.EquipmentType

    if equipment_type_obj != None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment Type with name: '{equipment_type.name}' already exist.")

    new_equipment_type = models.EquipmentType(name=equipment_type.name)
    new_equipment_type.created_by_user = current_user
    new_equipment_type.modified_by_user = current_user
    db.add(new_equipment_type)
    db.commit()

    for failure_name in equipment_type.failures:
        failure = db.query(models.EquipmentFailure).filter(models.EquipmentFailure.name == failure_name).first() # type: models.EquipmentFailure
        if not failure:
            failure = models.EquipmentFailure(name=failure_name)
            failure.created_by_user = current_user
            failure.modified_by_user = current_user
        new_equipment_type.add_failure(failure)
    db.commit()
    
    db.refresh(new_equipment_type)

    return new_equipment_type


@router.put("/{id}", response_model=schemas.EquipmentTypeOut)
async def update_equipment_type(id: int, equipment_type: schemas.EquipmentTypeIn, db: Session = Depends(get_session), current_user: models.User = Depends(login_manager)):
    query = db.query(models.EquipmentType).filter(models.EquipmentType.id == id)

    updated_equipment_type = query.first() # type: models.EquipmentType

    if not updated_equipment_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment Type with id: {id} does not exist.")

    query.update(equipment_type.dict(), synchronize_session=False)
    updated_equipment_type.modified_by_user = current_user
    updated_equipment_type.date_modified = datetime.now()
    updated_equipment_type.remove_all_failures()
    db.commit()

    for failure_name in equipment_type.failures:
        failure = db.query(models.EquipmentFailure).filter(models.EquipmentFailure.name == failure_name).first() # type: models.EquipmentFailure
        if not failure:
            failure = models.EquipmentFailure(name=failure_name)
            failure.created_by_user = current_user
            failure.modified_by_user = current_user
        updated_equipment_type.add_failure(failure)
    db.commit()

    db.refresh(updated_equipment_type)

    return updated_equipment_type


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipment_type(id: int, db: Session = Depends(get_session), current_user: models.User = Depends(login_manager)):
    equipment_type = db.query(models.EquipmentType).filter(models.EquipmentType.id == id).first() # type: models.EquipmentType

    if equipment_type == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment Type with id: {id} does not exist.")

    db.delete(equipment_type)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id}", response_model=schemas.EquipmentTypeOut)
async def get_equipment_type_by_id(id: int, db: Session = Depends(get_session)):
    equipment_type = db.query(models.EquipmentType).filter(models.EquipmentType.id == id).first() # type: models.EquipmentType
    if not equipment_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment Type with id: {id} does not exist.")

    return equipment_type


@router.get("/", response_model=schemas.EquipmentTypeListOut)
async def get_equipment_type(serial_number: str = "", db: Session = Depends(get_session)):
    equipment_types = db.query(models.EquipmentType).filter(models.EquipmentType.serial_number.ilike("%" + serial_number + "%")).all() # type: List[models.EquipmentType]
    return {"items": equipment_types}