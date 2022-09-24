from __future__ import annotations
from dataclasses import Field
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from cmms import enums


# TODO: Add descriptions.

class UserOut(BaseModel):
    id: int
    active: bool
    
    first_name: str
    last_name: str
    username: str
    date_created: datetime
    date_modified: datetime
    last_login_date: datetime=None
    email: str=None
    phone: str=None

    class Config:
        orm_mode = True


class UserListOut(BaseModel):
    items: List[UserOut]

    class Config:
        orm_mode = True


class AuditOut(BaseModel):
    date_created: datetime
    date_modified: datetime
    modified_by_user: Optional[UserOut] = None
    created_by_user: Optional[UserOut] = None


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    username: str
    password: str
    active: Optional[bool] = Field(default=True, description="If the user should be allowed to login.")
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None, description="Phone number maching '123-456-7890', '123.456.7890', '123 456 7890'", regex=r'(\d{3}[-\.\s]\d{3}[-\.\s]\d{4})')


class Token(BaseModel):
    access_token: str
    token_type: str
    expire_minutes: int
    expires: datetime


class TokenData(BaseModel):
    id: Optional[str] = None


class EquipmentFailureIn(BaseModel):
    name: str


class EquipmentFailureOut(AuditOut):
    id: int
    name: str

    class Config:
        orm_mode = True


class EquipmentTypeIn(BaseModel):
    name: str
    failures: List[str]


class EquipmentTypeOut(AuditOut):
    id: int
    name: str
    failures: List[EquipmentFailureOut]

    class Config:
        orm_mode = True


class ClassificationIn(BaseModel):
    name: str


class ClassificationOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class EquipmentIn(BaseModel):
    name: str
    brand: str
    model: str
    serial_number: str
    capacity: Optional[str] = ""
    code: Optional[str] = ""
    priority: Optional[str] = Field(default=enums.Priority.NA.value, description=f"Must be one of the following: {[item.name for item in enums.Priority]}")
    type_id: Optional[int] = None
    location_id: Optional[int] = None
    parent_equipment_id: Optional[int] = None
    acquisition_date: Optional[datetime] = datetime.now()
    year: Optional[int] = None
    classification1_name: Optional[str] = Field(default=None, description="Classification 1 name. Created if not exists.")
    classification2_name: Optional[str] = Field(default=None, description="Classification 2 name. Created if not exists.")
    maintenance_plan_id: Optional[int] = None


class EquipmentOut(AuditOut):
    id: int
    name: str
    brand: str
    model: str
    serial_number: str
    acquisition_date: datetime
    capacity: Optional[str] = ""
    code: Optional[str] = ""
    priority: Optional[enums.Priority] = enums.Priority.NA
    type_id: Optional[int] = None
    location_id: Optional[int] = None
    parent_equipment_id: Optional[int] = None
    year: Optional[int] = None
    classification1: Optional[ClassificationOut] = None
    classification2: Optional[ClassificationOut] = None
    maintenance_plan_id: Optional[int] = None

    class Config:
        orm_mode = True


class EquipmentListOut(BaseModel):
    items: List[EquipmentOut]

    class Config:
        orm_mode = True


class EquipmentTypeListOut(BaseModel):
    items: List[EquipmentTypeOut]

    class Config:
        orm_mode = True


class EquipmentFailureListOut(BaseModel):
    items: List[EquipmentFailureOut]

    class Config:
        orm_mode = True


class CauseOfEquipmentFailureIn(BaseModel):
    name: str
    read_only: Optional[bool] = False


class CauseOfEquipmentFailureOut(AuditOut):
    id: int
    name: str
    read_only: bool

    class Config:
        orm_mode = True


class CauseOfEquipmentFailureListOut(BaseModel):
    items: List[CauseOfEquipmentFailureOut]

    class Config:
        orm_mode = True


class MaintenanceActivityIn(BaseModel):
    name: str
    priority: enums.Priority = Field(default=enums.Priority.NA.value, description=f"Optional defaults to 'NA', must be one of the following: {[item.name for item in enums.Priority]}")
    work_type: enums.WorkType = Field(default=enums.WorkType.Preventive.value, description=f"Optional defaults to 'Preventive', must be one of the following: {[item.name for item in enums.WorkType]}")
    duration_hours: int = Field(0, description="Optional defaults to 0, time in hours to finish activity.")
    duration_minutes: int = Field(0, description="Optional defaults to 0, time in minutes to finish activity.")
    shutdown_duration_days: Optional[int] = Field(None, description="Optional defaults to None, time in days for shutdown.", gt=0)

    date_regimen: Optional[enums.MaintenanceActivityRegimen] = Field(None, description=f"Optional defaults to None, used to specify when to do activity based on dates. Must be one of the following or None if not used: {[item.name for item in enums.MaintenanceActivityRegimen]}")
    date_frequency: Optional[int] = Field(None, description="Required if 'date_regimen' is not None. How offtine to preform activity based on 'date_regimen'.")

    meter_unit_name: Optional[str] = Field(None, description="Optional defaults to None, used to specify when to do activity based on a meter reading. Set to None if not used.")
    meter_frequency: Optional[int] = Field(None, description="Required if 'meter_unit' is not None. How offtine to preform activity based on 'meter_unit' reading.")

    controlled_by_condition: Optional[bool] = Field(False, description="Optional defaults to False, Set True if activity is controlled by a Good, Fair, Bad condition.")

    controlled_by_measurement: Optional[bool] = Field(False, description="Optional defaults to False, Set True if activity is controlled by a measurement.")
    minium_measurement: Optional[float] = Field(None, description="Required if 'controlled_by_measurement' is not None and activity is controlled by a minimum measurement.")
    maximum_measurement: Optional[float] = Field(None, description="Required if 'controlled_by_measurement' is not None and activity is controlled by a maximum measurement.")
    measurement_unit: Optional[str] = Field(None, description="Required if 'controlled_by_measurement' is not None. Measurement unit of measure.")


class MaintenancePlanIn(BaseModel):
    name: str
    regimen: enums.MaintenancePlanRegimen = Field(enums.MaintenancePlanRegimen.DATE.value, description=f"Used to denote if activities are {[item.name for item in enums.MaintenancePlanRegimen]}")
    children: List[MaintenancePlanIn] = Field(None, description="A list of 'MaintenancePlanIn' that should be under this plan.")
    activities: List[MaintenanceActivityIn] = Field(None, description="A list of 'MaintenanceActivityIn' that should be under this plan.")


class MeterUnitOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class MaintenanceActivityOut(AuditOut):
    id: int
    name: str
    priority: enums.Priority = Field(default="", description=f"Optional defaults to '', must be one of the following: {[item.name for item in enums.Priority]}")
    work_type: enums.WorkType = Field(default=enums.WorkType.Preventive.value, description=f"Optional defaults to 'Preventive', must be one of the following: {[item.name for item in enums.WorkType]}")
    duration_hours: int = Field(0, description="Optional defaults to 0, time in hours to finish activity.")
    duration_minutes: int = Field(0, description="Optional defaults to 0, time in minutes to finish activity.")
    requires_shutdown: Optional[bool] = Field(False, description="Optional defaults to False, does activity require machine shutdown.")
    shutdown_duration_days: Optional[int] = Field(None, description="Optional defaults to None, time in days for shutdown.")

    date_regimen: Optional[enums.MaintenanceActivityRegimen] = Field(None, description=f"Optional defaults to None, used to specify when to do activity based on dates. Must be one of the following or None if not used: {[item.name for item in enums.MaintenanceActivityRegimen]}")
    date_frequency: Optional[int] = Field(None, description="Required if 'date_regimen' is not None. How offtine to preform activity based on 'date_regimen'.")

    meter_unit: Optional[MeterUnitOut] = Field(None, description="Optional defaults to None, used to specify when to do activity based on a meter reading. Set to None if not used.")
    meter_frequency: Optional[int] = Field(None, description="Required if 'meter_unit' is not None. How offtine to preform activity based on 'meter_unit' reading.")

    controlled_by_condition: Optional[bool] = Field(False, description="Optional defaults to False, Set True if activity is controlled by a Good, Ok, Bad condition.")

    controlled_by_measurement: Optional[bool] = Field(False, description="Optional defaults to False, Set True if activity is controlled by a measurement.")
    minium_measurement: Optional[float] = Field(None, description="Required if 'controlled_by_measurement' is not None and activity is controlled by a minimum measurement.")
    maximum_measurement: Optional[float] = Field(None, description="Required if 'controlled_by_measurement' is not None and activity is controlled by a maximum measurement.")
    measurement_unit: Optional[str] = Field(None, description="Required if 'controlled_by_measurement' is not None. Measurement unit of measure.")

    class Config:
        orm_mode = True


class UpdateMaintenanceActivityIn(BaseModel):
    id: int
    name: str
    priority: enums.Priority
    work_type: enums.WorkType
    duration_hours: int
    duration_minutes: int
    requires_shutdown: bool
    shutdown_duration_days: Optional[int]

    date_regimen: Optional[enums.MaintenanceActivityRegimen]
    date_frequency: Optional[int]

    meter_unit_name: Optional[str]
    meter_frequency: Optional[int]

    controlled_by_condition: bool

    controlled_by_measurement: bool
    minium_measurement: Optional[float]
    maximum_measurement: Optional[float]
    measurement_unit: Optional[str]

    class Config:
        orm_mode = True


class UpdateMaintenancePlanIn(BaseModel):
    id: int
    name: str
    regimen: enums.MaintenancePlanRegimen
    activities: List[UpdateMaintenanceActivityIn]

    class Config:
        orm_mode = True


class MaintenancePlanOut(AuditOut):
    id: int
    name: str
    regimen: enums.MaintenancePlanRegimen = Field(enums.MaintenancePlanRegimen.DATE.value, description=f"Used to denote if activities are {[item.name for item in enums.MaintenancePlanRegimen]}")
    children: List[MaintenancePlanOut] = None
    activities: List[MaintenanceActivityOut]

    class Config:
        orm_mode = True


class MaintenancePlanListOut(BaseModel):
    items: List[MaintenancePlanOut]

    class Config:
        orm_mode = True


class LocationIn(BaseModel):
    name: str
    children: List[LocationIn] = None


class LocationOut(AuditOut):
    id: int
    name: str
    children: List[LocationOut] = None

    class Config:
        orm_mode = True


class LocationListOut(BaseModel):
    items: List[LocationOut]

    class Config:
        orm_mode = True