from datetime import datetime
from typing import List
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, Path
from sqlalchemy.orm import Session
from .. import models, schemas
from cmms.database import get_session
from cmms.api.extensions import login_manager


router = APIRouter(
    prefix="/cause_of_equipment_failure",
    tags=['Cause Of Equipment Failure']
)


@router.post("/create", response_model=schemas.CauseOfEquipmentFailureOut)
async def create_cause_of_failure(cause_of_failure: schemas.CauseOfEquipmentFailureIn, db: Session = Depends(get_session), current_user: models.User = Depends(login_manager)):
    dict_ = cause_of_failure.dict()
    
    new_cause_of_failure = models.CauseOfEquipmentFailure(**dict_)
    new_cause_of_failure.created_by_user = current_user
    new_cause_of_failure.modified_by_user = current_user
    db.add(new_cause_of_failure)
    db.commit()
    db.refresh(new_cause_of_failure)
    return new_cause_of_failure


@router.put("/{id}", response_model=schemas.CauseOfEquipmentFailureOut)
async def update_cause_of_failure(id: int, cause_of_failure: schemas.CauseOfEquipmentFailureIn, db: Session = Depends(get_session), current_user: models.User = Depends(login_manager)):
    query = db.query(models.CauseOfEquipmentFailure).filter(models.CauseOfEquipmentFailure.id == id)

    updated_cause_of_failure = query.first() # type: models.CauseOfEquipmentFailure

    if not updated_cause_of_failure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cause Of Equipment Failure with id: {id} does not exist.")
    
    if updated_cause_of_failure.read_only:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Cause Of Equipment Failure has been set to read only, can not update.")

    query.update(cause_of_failure.dict(), synchronize_session=False)
    updated_cause_of_failure.modified_by_user = current_user
    updated_cause_of_failure.date_modified = datetime.now()

    db.commit()
    db.refresh(updated_cause_of_failure)

    return updated_cause_of_failure


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cause_of_failure(id: int, db: Session = Depends(get_session), current_user: models.User = Depends(login_manager)):
    query = db.query(models.CauseOfEquipmentFailure).filter(models.CauseOfEquipmentFailure.id == id)

    cause_of_failure = query.first() # type: models.CauseOfEquipmentFailure

    if cause_of_failure == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cause Of Equipment Failure with id: {id} does not exist.")
    
    if cause_of_failure.read_only:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Cause Of Equipment Failure with id: {id} is set to read only and can not be deleted.")

    query.delete(synchronize_session=False)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id}", response_model=schemas.CauseOfEquipmentFailureOut)
async def get_cause_of_failure_by_id(id: int, db: Session = Depends(get_session)):
    cause_of_failure = db.query(models.CauseOfEquipmentFailure).filter(models.CauseOfEquipmentFailure.id == id).first() # type: models.CauseOfEquipmentFailure
    if not cause_of_failure:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cause Of Equipment Failure with id: {id} does not exist.")

    return cause_of_failure


@router.get("/", response_model=schemas.CauseOfEquipmentFailureListOut)
async def get_cause_of_failure(name: str = "", db: Session = Depends(get_session)):
    cause_of_failures = db.query(models.CauseOfEquipmentFailure).filter(models.CauseOfEquipmentFailure.name.ilike("%" + name + "%")).all() # type: List[models.CauseOfEquipmentFailure]
    return {"items": cause_of_failures}