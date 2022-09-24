from __future__ import annotations
from email.policy import default
import logging
import bcrypt
import os
import base64
from enum import Enum as PythonEnum
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, String, ForeignKey, Boolean, UniqueConstraint, Enum, Table, Float, BLOB
from sqlalchemy.orm import relationship, validates, Session
from cmms.database import DeclarativeBase, get_session
from cmms.mixins import AuditMixin, NoteMixin
from cmms.enums import Priority, WorkType, MaintenancePlanRegimen, MaintenanceActivityRegimen, Impact, WOStatus
from cmms.config import DATETIME_FORMAT, ENCODING_STR
from cmms import errors


logger = logging.getLogger("backend")


class Base(DeclarativeBase):
    __abstract__ = True
    # __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)


class Status(Base):
    __abstract__ = True
    __table_args__ = {"sqlite_autoincrement": False}

    name = Column(String(50), nullable=False, unique=True)

    def __repr__(self):
        return f'<{self.__class__.name}(id={self.id}, name="{self.name}")>'
    
    def __str__(self) -> str:
        return self.name


class Type_(Base):
    __abstract__ = True

    name = Column(String(50), nullable=False, unique=True)

    def __repr__(self):
        return f'<{self.__class__.name}(id={self.id}, name="{self.name}")>'
    
    def __str__(self) -> str:
        return self.name


class Classification(Type_):
    __abstract__ = True

    name = Column(String(256), nullable=False, unique=True, index=True)


class FileData(Base, AuditMixin, NoteMixin):
    __tablename__ = "file_data"

    filename = Column(String(500), nullable=False, unique=True)
    original_filename = Column(String(500))
    note = Column(String(750), default="")
    data = Column(BLOB, nullable=False)

    def download(self, file_path: str) -> None:
        with open(file_path, "wb") as f:
            f.write(self.data)
        
    
    @staticmethod
    def create(filename: str, file_path: str, note: str=None) -> FileData:
        """Creates a new FileData obj. Note this does not save to db.

        Args:
            filename (str): Filename for this file.
            file_path (str): Current os file location.
            note (str, optional): Comments to add to file.

        Returns:
            FileData: Returns obj without saving to db.
        """
        origingal_filename = os.path.basename(file_path)
        
        with open(file_path, "rb") as f:
            file_data = base64.b64decode(f.read())

        note_obj = None
        if note:
            note_obj = Note(data=note)
            
        file_obj = FileData(
            filename=filename,
            origingal_filename=origingal_filename,
            data=file_data,
            note=note_obj
        )

        return file_obj


class ImageData(Base, AuditMixin, NoteMixin):
    __tablename__ = "image_data"

    filename = Column(String(500), nullable=False, unique=True)
    original_filename = Column(String(500))
    data = Column(BLOB, nullable=False)

    def download(self, file_path: str) -> None:
        with open(file_path, "wb") as f:
            f.write(self.data)
        
    
    @staticmethod
    def create(filename: str, file_path: str, note: str=None) -> ImageData:
        """Creates a new ImageData obj. Note this does not save to db.

        Args:
            filename (str): Filename for this file.
            file_path (str): Current os file location.
            note (str, optional): Comments to add to file.

        Returns:
            ImageData: Returns obj without saving to db.
        """
        origingal_filename = os.path.basename(file_path)
        
        with open(file_path, "rb") as f:
            file_data = base64.b64decode(f.read())

        note_obj = None
        if note:
            note_obj = Note(data=note)

        file_obj = ImageData(
            filename=filename,
            origingal_filename=origingal_filename,
            data=file_data,
            note=note_obj
        )

        return file_obj


class Note(Base):
    """Represents a note."""
    __tablename__ = "note"

    data = Column(String(2000))


class MeterUnit(Base):
    """Represents a meter unit."""
    __tablename__ = "meter_unit"

    name = Column(String(50))


class User(Base, AuditMixin):
    __tablename__ = 'user'

    active = Column(Boolean, nullable=False, default=True)
    last_login_date = Column(DateTime)
    email = Column(String(256))
    first_name = Column(String(15), nullable=False)
    last_name = Column(String(15), nullable=False)
    phone = Column(String(256))
    username = Column(String(256), nullable=False, unique=True, index=True)
    password_hash = Column(String(256), nullable=False)

    # Relationship

    def __repr__(self) -> str:
        return f"User('{self.username}', '{self.email}')"
    
    def __str__(self) -> str:
        return self.full_name
    
    def on_login(self) -> UserLoginLog:
        """Log a login event."""
        return UserLoginLog.create(event_type=LoginEventType.Login, user=self)
    
    def on_logout(self) -> UserLoginLog:
        """Log a logout event."""
        return UserLoginLog.create(event_type=LoginEventType.Logout, user=self)
    
    @property
    def last_login_date_str(self) -> str:
        return self.last_login_date.strftime(DATETIME_FORMAT)
    
    @property
    def password(self):
        """Prevent password from being accessed."""
        raise AttributeError('password is not a readable attribute!')
    
    @property
    def is_superuser(self) -> bool:
        """Check if the user is a superuser."""
        return self.id == 1

    @password.setter
    def password(self, password: str):
        """Hash password on the fly. This allows the plan text password to be used when creating a User instance."""
        self.password_hash = User.generate_password_hash(password)
    
    @property
    def full_name(self) -> str:
        """Return the full name of the user. In the following format: first_name, last_name"""
        return f"{self.first_name}, {self.last_name}"
    
    @property
    def initials(self) -> str:
        """Return the initials of the user."""
        return f"{self.first_name[0].upper()}{self.last_name[0].upper()}"
    
    def check_password(self, password: str) -> bool:
        return User.verify_password(self.password_hash, password)
    
    @staticmethod
    def verify_password(password_hash: str, password: str) -> bool:
        """Check if password matches the one provided."""
        return bcrypt.checkpw(password.encode(ENCODING_STR), password_hash.encode(ENCODING_STR))
    
    @staticmethod
    def generate_password_hash(password: str) -> str:
        """Generate a hashed password."""
        return bcrypt.hashpw(password.encode(ENCODING_STR), bcrypt.gensalt()).decode(ENCODING_STR)


class LoginEventType(PythonEnum):
    """Represents a user login log event type."""
    Login = "Login"
    Logout = "Logout"


class UserLoginLog(Base):
    """A simple log for tracking who logged in or out and when."""
    __tablename__ = 'user_login'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_date = Column(DateTime, nullable=False, default=datetime.now)
    event_type = Column(Enum(LoginEventType))
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    # Relationships
    user = relationship('User', foreign_keys=[user_id]) # type: User

    def __repr__(self) -> str:
        return f"<UserLoginLog(id={self.id}, event_date={self.event_date}, event_type={self.event_type}, user={self.user})>"
    
    def __str__(self) -> str:
        return f"{self.event_date} - {self.event_type} - {self.user}"

    @staticmethod
    def create(event_type: LoginEventType, user: User) -> UserLoginLog:
        """Create a new user login log."""
        log = UserLoginLog(event_type=event_type, user=user)
        return log

    @staticmethod
    def on_login(user: User) -> UserLoginLog:
        """Log a login event."""
        return UserLoginLog.create(event_type=LoginEventType.Login, user=user)
    
    @staticmethod
    def on_logout(user: User) -> UserLoginLog:
        """Log a logout event."""
        return UserLoginLog.create(event_type=LoginEventType.Logout, user=user)


class EquipmentClassification1(Base):
    __tablename__ = "equipment_classification1"
    
    name = Column(String(100), nullable=False, unique=True, index=True)


class EquipmentClassification2(Base):
    __tablename__ = "equipment_classification2"
    
    name = Column(String(100), nullable=False, unique=True, index=True)


class CauseOfEquipmentFailure(Base, AuditMixin):
    """Represents a cause of equipment failure."""
    __tablename__ = "cause_of_equipment_failure"

    name = Column(String(100), nullable=False, unique=True, index=True)
    read_only = Column(Boolean, nullable=False, default=False)

    @validates("name")
    def validates_name(self, key: str, value: str) -> str:
        if self.read_only:
            raise Exception("CauseOfEquipmentFailure is set to read only, can not edit.")
        return value


class EquipmentFailure(Base, AuditMixin):
    """Represents a type of equipment failure."""
    __tablename__ = "equipment_failure"

    name = Column(String(100), nullable=False, unique=True, index=True)


equipmenttypetofalure_table = Table(
    "equipment_type_to_failure",
    DeclarativeBase.metadata,
    Column("equipment_failure_id", ForeignKey("equipment_failure.id"), primary_key=True),
    Column("equipment_type_id", ForeignKey("equipment_type.id"), primary_key=True),
)


class EquipmentType(Base, AuditMixin):
    """Represents a type of equipment."""
    __tablename__ = "equipment_type"

    name = Column(String(256), nullable=False, unique=True, index=True)
    failures = relationship("EquipmentFailure", secondary=equipmenttypetofalure_table) # type: list[EquipmentFailure]

    def add_failure(self, failure: EquipmentFailure, user: User) -> None:
        if failure in self.failures:
            return
        self.modified_by_user = user
        self.failures.append(failure)
    
    def remove_failure(self, failure: EquipmentFailure, user: User) -> None:
        """Removes a failure from this equipment.

        Args:
            failure (EquipmentFailure): The failure to remove.
        """
        if failure not in self.failures:
            return
        self.failures.remove(failure)
        self.modified_by_user = user
    
    def remove_all_failures(self, user: User) -> None:
        """Removes all failures for this type."""
        self.failures.clear()
        self.modified_by_user = user


maintenanceplantofile_table = Table(
    "maintenance_plan_to_file",
    DeclarativeBase.metadata,
    Column("file_data_id", ForeignKey("file_data.id"), primary_key=True),
    Column("maintenance_plan_id", ForeignKey("maintenance_plan.id"), primary_key=True),
)


class MaintenancePlan(Base, AuditMixin, NoteMixin):
    """Represents a maintenance plan."""
    __tablename__ = "maintenance_plan"

    name = Column(String(256), nullable=False, index=True, unique=True)
    regimen = Column(Enum(MaintenancePlanRegimen), nullable=False, default=MaintenancePlanRegimen.DATE)
    parent_plan_id = Column(Integer, ForeignKey('maintenance_plan.id'))

    # Relationships
    children = relationship("MaintenancePlan", remote_side=parent_plan_id) # type: list[MaintenancePlan]
    activities = relationship("MaintenanceActivity", back_populates="plan") # type: list[MaintenanceActivity]
    files = relationship("FileData", secondary=maintenanceplantofile_table) # type: list[FileData]

    def __str__(self) -> str:
        return self.name

    @property
    def has_files(self) -> bool:
        return (self.files > 0)

    @property
    def is_parent(self) -> bool:
        """Returns True if this is the parent plan."""
        return self.parent_plan_id == None
    
    def add_child(self, child: MaintenancePlan, user: User) -> None:
        if child in self.children:
            return
        self.children.append(child)
        self.modified_by_user = user
    
    def remove_child(self, child: MaintenancePlan, user: User) -> None:
        if child not in self.children:
            return
        self.children.remove(child)
        self.modified_by_user = user

    def add_file(self, file_data: FileData, user: User) -> None:
        if file_data in self.files:
            return
        self.files.append(file_data)
        self.modified_by_user = user
    
    def remove_file(self, file_data: FileData, user: User) -> None:
        if file_data not in self.files:
            return
        self.files.remove(file_data)
        self.modified_by_user = user


maintenanceactivitytofile_table = Table(
    "maintenance_activity_to_file",
    DeclarativeBase.metadata,
    Column("file_data_id", ForeignKey("file_data.id"), primary_key=True),
    Column("maintenance_activity_to_file_id", ForeignKey("maintenance_activity.id"), primary_key=True),
)


maintenanceactivitytoimage_table = Table(
    "maintenance_activity_to_image",
    DeclarativeBase.metadata,
    Column("image_data_id", ForeignKey("image_data.id"), primary_key=True),
    Column("maintenance_activity_to_image_id", ForeignKey("maintenance_activity.id"), primary_key=True),
)


class MaintenanceActivity(Base, AuditMixin, NoteMixin):
    """Represents a maintenance activity for a maintenance plan."""
    __tablename__ = "maintenance_activity"
    __table_args__ = (
        UniqueConstraint("name", "plan_id"),
    )

    name = Column(String(256), nullable=False)
    plan_id = Column(Integer, ForeignKey('maintenance_plan.id'))
    priority = Column(Enum(Priority), nullable=False, default=Priority.NA)
    work_type = Column(Enum(WorkType), nullable=False)
    duration_hours = Column(Integer)
    duration_minutes = Column(Integer)
    requires_shutdown = Column(Boolean, nullable=False, default=False)
    shutdown_duration_days = Column(Integer)
    date_regimen = Column(Enum(MaintenanceActivityRegimen), default=MaintenanceActivityRegimen.DAYS)
    date_frequency = Column(Integer)
    meter_unit_id = Column(Integer, ForeignKey('meter_unit.id'))
    meter_frequency = Column(Integer)
    controlled_by_condition = Column(Boolean, nullable=False, default=False)
    controlled_by_measurement = Column(Boolean, nullable=False, default=False)
    minium_measurement = Column(Float)
    maximum_measurement = Column(Float)
    measurement_unit = Column(String(50))

    # Relationships
    plan = relationship("MaintenancePlan", foreign_keys=[plan_id]) # type: MaintenancePlan
    meter_unit = relationship("MeterUnit", foreign_keys=[meter_unit_id]) # type: MeterUnit
    files = relationship("FileData", secondary=maintenanceactivitytofile_table) # type: list[FileData]
    images = relationship("ImageData", secondary=maintenanceactivitytoimage_table) # type: list[ImageData]
    
    @property
    def has_files(self) -> bool:
        return (self.files > 0)
    
    @property
    def has_images(self) -> bool:
        return (self.images > 0)
    
    @validates("shutdown_duration_days")
    def validates_shutdown_duration_days(self, key: str, value: int) -> int:
        if not value: return value
        if value <= 0 and self.requires_shutdown == True:
            raise ValueError("shutdown_duration_days can not be equal to or less then 0.")
        return value

    @validates("requires_shutdown")
    def validates_requires_shutdown(self, key: str, value: bool) -> bool:
        return (self.shutdown_duration_days != None)
    
    @validates("controlled_by_condition")
    def validates_controlled_by_condition(self, key: str, value: bool) -> bool:
        if value and self.controlled_by_measurement:
            raise Exception("MaintenanceActivity must be controlled by eather a condition or measurement.")
        elif not value and not self.controlled_by_measurement:
            self.minium_measurement = None
            self.maximum_measurement = None
            self.measurement_unit = None
        if value:
            self.work_type = WorkType.Predictive
        else:
            self.work_type = WorkType.Preventive
        return value
    
    @validates("controlled_by_measurement")
    def validates_controlled_by_measurement(self, key: str, value: bool) -> bool:
        if value and self.controlled_by_condition:
            raise Exception("MaintenanceActivity must be controlled by eather a condition or measurement.")
        elif not value and not self.controlled_by_condition:
            self.minium_measurement = None
            self.maximum_measurement = None
            self.measurement_unit = None
        if value:
            self.work_type = WorkType.Predictive
        else:
            self.work_type = WorkType.Preventive
        return value

    def add_file(self, file_data: FileData, user: User) -> None:
        if file_data in self.files:
            return
        self.files.append(file_data)
        self.modified_by_user = user
    
    def add_image(self, image_data: ImageData, user: User) -> None:
        if image_data in self.images:
            return
        self.images.append(image_data)
        self.modified_by_user = user
    
    def remove_file(self, file_data: FileData, user: User) -> None:
        if file_data not in self.files:
            return
        self.files.remove(file_data)
        self.modified_by_user = user
    
    def remove_image(self, image_data: ImageData, user: User) -> None:
        if image_data not in self.images:
            return
        self.images.remove(image_data)
        self.modified_by_user = user
    

equipmenttofile_table = Table(
    "equipment_to_file",
    DeclarativeBase.metadata,
    Column("file_data_id", ForeignKey("file_data.id"), primary_key=True),
    Column("equipment_id", ForeignKey("equipment.id"), primary_key=True),
)


equipmenttoimage_table = Table(
    "equipment_to_image",
    DeclarativeBase.metadata,
    Column("image_data_id", ForeignKey("image_data.id"), primary_key=True),
    Column("equipment_id", ForeignKey("equipment.id"), primary_key=True),
)


class Equipment(Base, AuditMixin, NoteMixin):
    """Represents a piece of equipment."""
    __tablename__ = "equipment"
    __table_args__ = (
        UniqueConstraint("name", "brand", "model", "serial_number"),
    )

    name = Column(String(256), nullable=False, index=True)
    capacity = Column(String(100), default="")
    code = Column(String(100), default="")
    brand = Column(String(100), nullable=False, index=True)
    model = Column(String(100), nullable=False, index=True)
    serial_number = Column(String(256), nullable=False, index=True)
    priority = Column(Enum(Priority), nullable=False, default=Priority.NA)
    type_id = Column(Integer, ForeignKey('equipment_type.id'))
    location_id = Column(Integer, ForeignKey('location.id'))
    parent_equipment_id = Column(Integer, ForeignKey('equipment.id'))
    acquisition_date = Column(DateTime, nullable=False, default=datetime.now())
    year = Column(Integer)
    classification1_id = Column(Integer, ForeignKey('equipment_classification1.id'))
    classification2_id = Column(Integer, ForeignKey('equipment_classification2.id'))
    maintenance_plan_id = Column(Integer, ForeignKey('maintenance_plan.id'))

    # Relationships
    type_ = relationship("EquipmentType", foreign_keys=[type_id]) # type: EquipmentType
    location = relationship("Location", foreign_keys=[location_id], back_populates="equipment") # type: Location
    parent_equipment = relationship("Equipment", foreign_keys=[parent_equipment_id]) # type: Equipment
    files = relationship("FileData", secondary=equipmenttofile_table) # type: list[FileData]
    images = relationship("ImageData", secondary=equipmenttoimage_table) # type: list[ImageData]
    classification1 = relationship("EquipmentClassification1", foreign_keys=[classification1_id]) # type: EquipmentClassification1
    classification2 = relationship("EquipmentClassification2", foreign_keys=[classification2_id]) # type: EquipmentClassification2

    @property
    def has_maintenance_plan(self) -> bool:
        """Returns True if equipment has a maintenance plan."""
        return self.maintenance_plan_id != None
    
    @property
    def has_files(self) -> bool:
        return self.files > 0
    
    @property
    def has_images(self) -> bool:
        return self.images > 0

    def add_file(self, file_data: FileData, user: User) -> None:
        """Adds a file obj."""
        if file_data in self.files:
            return
        self.modified_by_user = user
        self.files.append(file_data)
    
    def add_image(self, image_data: ImageData, user: User) -> None:
        """Adds a image obj."""
        if image_data in self.images:
            return
            self.modified_by_user = user
        self.images.append(image_data)
    
    def remove_file(self, file_data: FileData, user: User) -> None:
        """Removes a file obj."""
        if file_data not in self.files:
            return
            self.modified_by_user = user
        self.files.remove(file_data)
    
    def remove_image(self, image_data: ImageData, user: User) -> None:
        """Removes a image obj."""
        if image_data not in self.images:
            return
            self.modified_by_user = user
        self.images.remove(image_data)
    
    def set_type(self, type_: EquipmentType, user: User) -> None:
        """Sets the equipment type."""
        self.modified_by_user = user
        self.type_ = type_
    
    def remove_type(self, user: User) -> None:
        """Removes the equipment type."""
        self.modified_by_user = user
        self.type_ = None
    
    def set_parent(self, parent_equipment: Equipment, user: User) -> None:
        """Sets the parent equipment."""
        self.modified_by_user = user
        self.parent_equipment = parent_equipment
    
    def remove_parent(self, user: User) -> None:
        """Removes parent equipment."""
        self.modified_by_user = user
        self.parent_equipment = None
    
    def set_classification1(self, classification1: Classification, user: User) -> None:
        """Sets the equipment classification1."""
        self.modified_by_user = user
        self.classification1 = classification1
    
    def remove_classification1(self, user: User) -> None:
        """Removes the equipment classification1."""
        self.modified_by_user = user
        self.classification1 = None
    
    def set_classification2(self, classification2: Classification, user: User) -> None:
        """Sets the equipment classification2."""
        self.modified_by_user = user
        self.classification2 = classification2
    
    def remove_classification2(self, user: User) -> None:
        """Removes the equipment classification2."""
        self.modified_by_user = user
        self.classification2 = None


locationtofile_table = Table(
    "location_to_file",
    DeclarativeBase.metadata,
    Column("file_data_id", ForeignKey("file_data.id"), primary_key=True),
    Column("location_id", ForeignKey("location.id"), primary_key=True),
)


locationtoimage_table = Table(
    "location_to_image",
    DeclarativeBase.metadata,
    Column("image_data_id", ForeignKey("image_data.id"), primary_key=True),
    Column("location_id", ForeignKey("location.id"), primary_key=True),
)


class Location(Base, AuditMixin, NoteMixin):
    """Represents a location."""
    __tablename__ = "location"

    name = Column(String(256), nullable=False, index=True, unique=True)
    parent_location_id = Column(Integer, ForeignKey('location.id'))

    # Relationships
    children = relationship("Location", remote_side=parent_location_id) # type: list[Location]
    equipment = relationship("Equipment", back_populates="location") # type: list[Equipment]
    files = relationship("FileData", secondary=locationtofile_table) # type: list[FileData]
    images = relationship("ImageData", secondary=locationtoimage_table) # type: list[ImageData]

    @staticmethod
    def root() -> Location:
        """Returns the root location."""
        db = get_session()
        location = db.query(Location).filter(Location.name == "Root").first()
        db.expunge(location)
        return location

    @property
    def has_files(self) -> bool:
        return (self.files > 0)
    
    @property
    def has_images(self) -> bool:
        return (self.images > 0)
    
    @property
    def is_parent(self) -> bool:
        """Returns True if this is the parent location."""
        return self.parent_location_id == None
    
    def add_child(self, child: Location, user: User) -> None:
        root_location = Location.root()
        if self.id == root_location.id:
            # TODO: Change exception.
            raise errors.CMMSError("Can not add root location to child locations.")

        if child in self.children:
            return
        self.children.append(child)
        self.modified_by_user = user
    
    def remove_child(self, child: Location, user: User) -> None:
        if child not in self.children:
            return
        self.children.remove(child)
        self.modified_by_user = user
    
    def delete(self, session: Session, user: User) -> None:
        root_location = Location.root()
        if self.id == root_location.id:
            # TODO: Change exception.
            raise errors.CMMSError("Can not delete root location.")
        for child in self.children:
            self.remove_child(child, user)
        
        session.delete(self)
        session.commit()
        
    def add_file(self, file_data: FileData, user: User) -> None:
        if file_data in self.files:
            return
        self.files.append(file_data)
        self.modified_by_user = user
    
    def add_image(self, image_data: ImageData, user: User) -> None:
        if image_data in self.images:
            return
        self.images.append(image_data)
        self.modified_by_user = user
    
    def remove_file(self, file_data: FileData, user: User) -> None:
        if file_data not in self.files:
            return
        self.files.remove(file_data)
        self.modified_by_user = user
    
    def remove_image(self, image_data: ImageData, user: User) -> None:
        if image_data not in self.images:
            return
        self.images.remove(image_data)
        self.modified_by_user = user


nonroutinejobtofile_table = Table(
    "nonroutine_job_to_file",
    DeclarativeBase.metadata,
    Column("file_data_id", ForeignKey("file_data.id"), primary_key=True),
    Column("nonroutine_job_id", ForeignKey("nonroutine_job.id"), primary_key=True),
)


nonroutinejobtoimage_before_table = Table(
    "nonroutine_job_to_image_before",
    DeclarativeBase.metadata,
    Column("image_data_id", ForeignKey("image_data.id"), primary_key=True),
    Column("nonroutine_job_id", ForeignKey("nonroutine_job.id"), primary_key=True),
)


nonroutinejobtoimage_after_table = Table(
    "nonroutine_job_to_image_after",
    DeclarativeBase.metadata,
    Column("image_data_id", ForeignKey("image_data.id"), primary_key=True),
    Column("nonroutine_job_id", ForeignKey("nonroutine_job.id"), primary_key=True),
)


class NonRoutineJob(Base, AuditMixin):
    """Represents a non-routine job."""
    __tablename__ = "nonroutine_job"

    reported_by = Column(String(100), nullable=False, default="")
    work_type = Column(Enum(WorkType), nullable=False, default=WorkType.Corrective)
    date_noticed = Column(DateTime, nullable=False, default=datetime.now())
    date_scheduled = Column(DateTime, nullable=False, default=datetime.now())
    equipment_id = Column(Integer, ForeignKey('equipment.id'), nullable=False)
    request_or_failure = Column(String(256), nullable=False)
    observations = Column(String(2000), nullable=False, default="")
    priority = Column(Enum(Priority), nullable=False, default=Priority.Low)
    work_preformed = Column(Boolean, nullable=False, default=False)
    date_started = Column(DateTime, nullable=False, default=datetime.now())
    date_finished = Column(DateTime)
    total_time_minutes = Column(Integer)
    estimated_time_minutes = Column(Integer)
    requires_shutdown = Column(Boolean, nullable=False, default=False)
    shutdown_duration_days = Column(Integer)
    equipment_stopped = Column(Boolean, nullable=False, default=False)
    other_equipment_stopped = Column(Boolean, nullable=False, default=False)
    caused_impact = Column(Boolean, nullable=False, default=False)
    impact_type = Column(Enum(Impact))
    impact_description = Column(String(2000), nullable=False, default="")
    procedure_description = Column(String(2000), nullable=False, default="")
    is_failure = Column(Boolean, nullable=False, default=False)
    failure_id = Column(Integer, ForeignKey('equipment_failure.id'))
    failure_cause_id = Column(Integer, ForeignKey('cause_of_equipment_failure.id'))
    work_order_id = Column(Integer, ForeignKey('work_order.id'))


    # Relationships
    equipment = relationship("Equipment", foreign_keys=[equipment_id]) # type: Equipment
    failure = relationship("EquipmentFailure", foreign_keys=[failure_id]) # type: EquipmentFailure
    failure_cause = relationship("CauseOfEquipmentFailure", foreign_keys=[failure_cause_id]) # type: CauseOfEquipmentFailure
    work_order = relationship("WorkOrder", foreign_keys=[work_order_id]) # type: WorkOrder
    files = relationship("FileData", secondary=nonroutinejobtofile_table) # type: list[FileData]
    before_images = relationship("ImageData", secondary=nonroutinejobtoimage_before_table) # type: list[ImageData]
    after_images = relationship("ImageData", secondary=nonroutinejobtoimage_after_table) # type: list[ImageData]


    @validates("shutdown_duration_days")
    def validates_shutdown_duration_days(self, key: str, value: int) -> int:
        if value <= 0:
            raise ValueError("shutdown_duration_days can not be equal to or less then 0.")
        self.requires_shutdown = True
        return value

    @validates("requires_shutdown")
    def validates_requires_shutdown(self, key: str, value: bool) -> bool:
        return (self.shutdown_duration_days != None)

    @validates("caused_impact")
    def validates_caused_impact(self, key: str, value: bool) -> bool:
        if value and self.impact_type == None:
            raise Exception("impact_type must be set if caused_impact is True.")
        return value
    
    @validates("is_failure")
    def validates_is_failure(self, key: str, value: bool) -> bool:
        if value and self.failure_id == None:
            raise Exception("A failure must be set if is_failure is True.")
        elif value and self.failure_cause_id == None:
            raise Exception("A failure cause must be set if is_failure is True.")
        return value

    def add_file(self, file_data: FileData, user: User) -> None:
        if file_data in self.files:
            return
        self.files.append(file_data)
        self.modified_by_user = user
    
    def remove_file(self, file_data: FileData, user: User) -> None:
        if file_data not in self.files:
            return
        self.files.remove(file_data)
        self.modified_by_user = user

    def add_before_image(self, image_data: ImageData, user: User) -> None:
        if image_data in self.before_images:
            return
        self.before_images.append(image_data)
        self.modified_by_user = user
    
    def remove_before_image(self, image_data: ImageData, user: User) -> None:
        if image_data not in self.before_images:
            return
        self.before_images.remove(image_data)
        self.modified_by_user = user
    
    def add_after_image(self, image_data: ImageData, user: User) -> None:
        if image_data in self.after_images:
            return
        self.after_images.append(image_data)
        self.modified_by_user = user
    
    def remove_after_image(self, image_data: ImageData, user: User) -> None:
        if image_data not in self.after_images:
            return
        self.after_images.remove(image_data)
        self.modified_by_user = user


workordertoequipment_table = Table(
    "work_order_to_equipment",
    DeclarativeBase.metadata,
    Column("work_order_id", ForeignKey("work_order.id"), primary_key=True),
    Column("equipment_id", ForeignKey("equipment.id"), primary_key=True),
)


class WorkOrder(Base, AuditMixin):
    """Represents a work order"""
    __tablename__ = "work_order"

    number = Column(String(100), nullable=False, unique=True, index=True)
    responsable = Column(String(100))
    status = Column(Enum(WOStatus), nullable=False, default=WOStatus.Open)
    date_closed = Column(DateTime)

    # Relationships
    equipment = relationship("Equipment", secondary=workordertoequipment_table) # type: list[Equipment]
    items = relationship("WorkOrderItem", back_populates="work_order") # type: list[WorkOrderItem]

    def add_equipment(self, equipment: Equipment, user: User):
        if equipment in self.equipment:
            return
        self.equipment.append(equipment)
        self.modified_by_user = user
    
    def remove_equipment(self, equipment: Equipment, user: User):
        if equipment not in self.equipment:
            return
        self.equipment.remove(equipment)
        self.modified_by_user = user


class WorkOrderItem(Base, AuditMixin, NoteMixin):
    """Represents a work order item"""
    __tablename__ = "work_order_item"

    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=False)
    maintenance_activity_id = Column(Integer, ForeignKey('maintenance_activity.id'), nullable=False)
    activity_name = Column(String(256), nullable=False)
    priority = Column(Enum(Priority), nullable=False, default=Priority.NA)
    work_type = Column(Enum(WorkType), nullable=False)
    estimated_duration_hours = Column(Integer, default=0)
    estimated_duration_minutes = Column(Integer, default=0)

    # Relationships
    work_order = relationship("WorkOrder", back_populates="items") # type: WorkOrder