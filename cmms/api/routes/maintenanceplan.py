from datetime import datetime
from typing import List
from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, Path
from sqlalchemy.orm import Session

from ...enums import WorkType
from .. import models, schemas
from cmms.database import get_session
from cmms.api.extensions import login_manager


router = APIRouter(
    prefix="/maintenance_plan",
    tags=['Maintenance Plan']
)


@router.post("/create", response_model=schemas.MaintenancePlanOut)
async def create_maintenance_plan(maintenance_plan: schemas.MaintenancePlanIn, db: Session = Depends(get_session), current_user: models.User = Depends(login_manager)):
    def create_plan(plan: dict) -> models.MaintenancePlan:
        plan_obj = db.query(models.MaintenancePlan).filter(models.MaintenancePlan.name == plan["name"]).first() # type: models.MaintenancePlan
        if plan_obj:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Maintenance Plan '{plan['name']}' already exists.")
        
        children = plan.pop("children", None) # type: list[dict]
        activities = plan.pop("activities", None) # type: list[dict]

        maintenance_plan = models.MaintenancePlan(**plan)
        maintenance_plan.created_by_user = current_user
        maintenance_plan.modified_by_user = current_user
        db.add(maintenance_plan)

        if activities and len(activities) > 0:
            for activity_dict in activities:
                meter_unit_name = activity_dict.pop("meter_unit_name", None) # type: str

                if meter_unit_name:
                    meter_unit = db.query(models.MeterUnit).filter(models.MeterUnit.name == meter_unit_name).first()
                    if not meter_unit:
                        meter_unit = models.MeterUnit(name=meter_unit_name)
                        db.add(meter_unit)
                else:
                    meter_unit = None
                activity_dict["meter_unit"] = meter_unit
                
                if activity_dict["shutdown_duration_days"] and activity_dict["shutdown_duration_days"] > 0:
                    activity_dict["requires_shutdown"] = True
                elif activity_dict["shutdown_duration_days"] and activity_dict["shutdown_duration_days"] <= 0:
                    activity_dict["shutdown_duration_days"] = None
                    activity_dict["requires_shutdown"] = False
                
                if not ((activity_dict["date_regimen"] and activity_dict["date_frequency"]) \
                    or (activity_dict["meter_unit"] and activity_dict["meter_frequency"]) \
                    or (activity_dict["date_regimen"] and activity_dict["date_frequency"] and  activity_dict["meter_unit"] and activity_dict["meter_frequency"])):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Maintenance Plan activity '{plan['name']}'-'{activity_dict['name']}' must a frequency type. Eather date_frequency and/or meter_frequency."
                        )

                if activity_dict["controlled_by_condition"] and activity_dict["controlled_by_measurement"]:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Maintenance Plan activity '{plan['name']}'-'{activity_dict['name']}' can only be controlled by a condition or measurement."
                        )

                if activity_dict["controlled_by_measurement"]:
                    activity_dict["work_type"] = WorkType.Predictive.name

                    if not activity_dict["minium_measurement"] and not activity_dict["maximum_measurement"]:
                        raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Maintenance Plan activity '{plan['name']}'-'{activity_dict['name']}' is controlled by a measurement but no min and/or max value was defined."
                        )

                    if activity_dict["minium_measurement"] == activity_dict["maximum_measurement"]:
                        raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Maintenance Plan activity '{plan['name']}'-'{activity_dict['name']}' is controlled by a measurement but min and max can not be the same."
                        )

                    if not activity_dict["measurement_unit"]:
                        raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Maintenance Plan activity '{plan['name']}'-'{activity_dict['name']}' is controlled by a measurement but no measurement_unit was defined."
                        )

                if activity_dict["controlled_by_condition"]:
                    activity_dict["work_type"] = WorkType.Predictive.name
                    activity_dict["minium_measurement"] = None
                    activity_dict["maximum_measurement"] = None

                
                maintenance_activity = models.MaintenanceActivity(**activity_dict)
                maintenance_activity.created_by_user = current_user
                maintenance_activity.modified_by_user = current_user
                maintenance_activity.plan = maintenance_plan
                maintenance_activity.work_type = activity_dict["work_type"] # Had to do this to get the type to change.
                db.add(maintenance_activity)
        
        if children and len(children) > 0:
            db.commit()
            for child_plan in children:
                child_plan_obj = create_plan(plan=child_plan)
                child_plan_obj.parent_plan_id = maintenance_plan.id
                db.commit()
        else:
            db.commit()
            db.refresh(maintenance_plan)
        
        return maintenance_plan
                    
    return create_plan(plan=maintenance_plan.dict())


@router.put("/{id}", response_model=schemas.MaintenancePlanOut)
async def update_maintenance_plan(id: int, maintenance_plan: schemas.UpdateMaintenancePlanIn, db: Session = Depends(get_session), current_user: models.User = Depends(login_manager)):
    maintenance_plan_obj = db.query(models.MaintenancePlan).filter(models.MaintenancePlan.id == id).first() # type: models.MaintenancePlan

    def update_plan(plan: dict) -> models.MaintenancePlan:
        plan_query = db.query(models.MaintenancePlan).filter(models.MaintenancePlan.id == plan["id"])
        plan_obj = plan_query.first() # type: models.MaintenancePlan

        if not plan_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Maintenance Plan id {plan['id']} does not exists.")
        
        children = plan.pop("children", None) # type: list[dict]
        activities = plan.pop("activities", None) # type: list[dict]

        if activities and len(activities) > 0:
            for activity_dict in activities:
                meter_unit_name = activity_dict.pop("meter_unit_name", None) # type: str

                if meter_unit_name:
                    meter_unit = db.query(models.MeterUnit).filter(models.MeterUnit.name == meter_unit_name).first()
                    if not meter_unit:
                        meter_unit = models.MeterUnit(name=meter_unit_name)
                        db.add(meter_unit)
                        db.commit()
                    activity_dict["meter_unit_id"] = meter_unit.id
                else:
                    activity_dict["meter_unit_id"] = None
                
                if activity_dict["shutdown_duration_days"] and activity_dict["shutdown_duration_days"] > 0:
                    activity_dict["requires_shutdown"] = True
                elif activity_dict["shutdown_duration_days"] and activity_dict["shutdown_duration_days"] <= 0:
                    activity_dict["shutdown_duration_days"] = None
                    activity_dict["requires_shutdown"] = False
                
                if not ((activity_dict["date_regimen"] and activity_dict["date_frequency"]) \
                    or (activity_dict["meter_unit_id"] and activity_dict["meter_frequency"]) \
                    or (activity_dict["date_regimen"] and activity_dict["date_frequency"] and  activity_dict["meter_unit_id"] and activity_dict["meter_frequency"])):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Maintenance Plan activity '{plan['name']}'-'{activity_dict['name']}' must a frequency type. Eather date_frequency and/or meter_frequency."
                        )

                if activity_dict["controlled_by_condition"] and activity_dict["controlled_by_measurement"]:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Maintenance Plan activity '{plan['name']}'-'{activity_dict['name']}' can only be controlled by a condition or measurement."
                        )

                if activity_dict["controlled_by_measurement"]:
                    activity_dict["work_type"] = WorkType.Predictive.name

                    if not activity_dict["minium_measurement"] and not activity_dict["maximum_measurement"]:
                        raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Maintenance Plan activity '{plan['name']}'-'{activity_dict['name']}' is controlled by a measurement but no min and/or max value was defined."
                        )

                    if activity_dict["minium_measurement"] == activity_dict["maximum_measurement"]:
                        raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Maintenance Plan activity '{plan['name']}'-'{activity_dict['name']}' is controlled by a measurement but min and max can not be the same."
                        )

                    if not activity_dict["measurement_unit"]:
                        raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Maintenance Plan activity '{plan['name']}'-'{activity_dict['name']}' is controlled by a measurement but no measurement_unit was defined."
                        )

                if activity_dict["controlled_by_condition"]:
                    activity_dict["work_type"] = WorkType.Predictive.name
                    activity_dict["minium_measurement"] = None
                    activity_dict["maximum_measurement"] = None

                activity_id = activity_dict["id"]
                maintenance_activity_query = db.query(models.MaintenanceActivity).filter(models.MaintenanceActivity.id == activity_id)
                maintenance_activity = maintenance_activity_query.first() # type: models.MaintenanceActivity
                
                if not maintenance_activity:
                    maintenance_activity = models.MaintenanceActivity(**activity_dict)
                    maintenance_activity.created_by_user = current_user
                    maintenance_activity.modified_by_user = current_user
                    maintenance_activity.plan = plan_obj
                    maintenance_activity.work_type = activity_dict["work_type"] # Had to do this to get the type to change.
                    db.add(maintenance_activity)
                    db.commit()
                else:
                    maintenance_activity_query.update(activity_dict, synchronize_session=False)
                    maintenance_activity.modified_by_user = current_user
                    maintenance_activity.date_modified = datetime.now()
                    maintenance_activity.plan = plan_obj
                    maintenance_activity.work_type = activity_dict["work_type"] # Had to do this to get the type to change.
                    db.commit()
        
        plan_query.update(plan, synchronize_session=False)
        db.refresh(plan_obj)
        plan_obj.modified_by_user = current_user
        plan_obj.date_modified = datetime.now()
        db.commit()

        if children and len(children) > 0:
            for child_plan in children:
                child_plan_obj = update_plan(plan=child_plan)
                child_plan_obj.parent_plan_id = plan_obj.id
                db.commit()
        
        db.refresh(maintenance_plan_obj)
        maintenance_plan_obj.modified_by_user = current_user
        maintenance_plan_obj.date_modified = datetime.now()
        db.commit()
        return maintenance_plan_obj
                    
    return update_plan(plan=maintenance_plan.dict())


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_maintenance_plan(id: int, db: Session = Depends(get_session), current_user: models.User = Depends(login_manager)):
    maintenance_plan = db.query(models.MaintenancePlan).filter(models.MaintenancePlan.id == id).first() # type: models.MaintenancePlan

    if maintenance_plan == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipment with id: {id} does not exist.")

    def delete_plan(plan: models.MaintenancePlan) -> None:
        if len(plan.children) > 0:
            for child in plan.children:
                for activity in child.activities:
                    db.delete(activity)
                delete_plan(child)
                db.delete(child)
        else:
            for activity in plan.activities:
                db.delete(activity)
        db.delete(plan)
    
    delete_plan(maintenance_plan)

    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id}", response_model=schemas.MaintenancePlanOut)
async def get_plan(id: int, db: Session = Depends(get_session)):
    plan = db.query(models.MaintenancePlan).filter(models.MaintenancePlan.id == id).first() # type: models.MaintenancePlan
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MaintenancePlan with id: {id} does not exist.")

    return plan


@router.get("/", response_model=schemas.MaintenancePlanListOut)
async def get_plan(name: str = "", db: Session = Depends(get_session)):
    plans = db.query(models.MaintenancePlan).filter(models.MaintenancePlan.name.ilike("%" + name + "%")).all() # type: list[models.MaintenancePlan]
    return {"items": plans}