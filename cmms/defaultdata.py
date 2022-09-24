import logging
import json
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from cmms.config import *
from cmms.database import DBContext
from cmms import models


logger = logging.getLogger("backend")


def load_default_data() -> None:
    logger.info("[SYSTEM] Checking default data.")

    with DBContext() as session:
        try:
            user_obj = models.User(**default_user)
            session.add(user_obj)
            session.commit()
        except IntegrityError:
            session.rollback()
            user_obj = session.query(models.User).filter(models.User.username == default_user["username"]).first()

        try:
            root_location = models.Location(name="Root")
            root_location.created_by_user_id = user_obj.id
            root_location.modified_by_user_id = user_obj.id
            session.add(root_location)
            session.commit()
        except IntegrityError:
            session.rollback()

        try:
            for cause_of_failure in cause_of_failures:
                item = models.CauseOfEquipmentFailure(name=cause_of_failure, read_only=True)
                item.created_by_user_id = user_obj.id
                item.modified_by_user_id = user_obj.id
                session.add(item)
            session.commit()
        except IntegrityError:
            session.rollback()

        try:
            for equipment_failure in equipment_failures:
                item = models.EquipmentFailure(name=equipment_failure)
                item.created_by_user_id = user_obj.id
                item.modified_by_user_id = user_obj.id
                session.add(item)
            session.commit()
        except IntegrityError:
            session.rollback()
        
        try:
            for equipment_type in equipment_types:
                name = equipment_type["name"]
                failures = equipment_type["failures"]

                equipment_type_obj = models.EquipmentType(name=name)
                for failure in failures:
                    failure_obj = session.query(models.EquipmentFailure).filter(models.EquipmentFailure.name == failure).first() # type: models.EquipmentFailure
                    equipment_type_obj.add_failure(failure_obj, user_obj)
                    item.created_by_user_id = user_obj.id
                session.add(equipment_type_obj)
            session.commit()
        except IntegrityError:
            session.rollback()


def load_test_data() -> None:
    logger.warning("[SYSTEM] Loading test data")
    with open("test_data.json", "r") as f:
        data = json.loads(f.read())
    
    locations = data.pop("Locations", None) # type: list[dict[str, str]]

    if locations:
        with DBContext() as session:
            root_location = models.Location(
                    name="Root"
                )

            session.add(root_location)
            session.commit()

            location_objs = {} # type: dict[str, models.Location]

            for location in locations:
                name = location["Name"]
                parent_location_name = location["Parent Location"]

                if parent_location_name == "Root":
                    location_obj = models.Location(
                        name=name,
                        parent_location_id=root_location.id
                    )

                else:
                    location_obj = models.Location(
                        name=name,
                        parent_location_id=location_objs[parent_location_name].id
                    )
                
                
                session.add(location_obj)
                session.commit()
                location_objs[location_obj.name] = location_obj

    equipment_classification1 = data.pop("Equipment Classifications 1", None) # type: list[str]

    if equipment_classification1:
        with DBContext() as session:
            for item in equipment_classification1:
                classification1 = models.EquipmentClassification1(name=item)
                session.add(classification1)
            session.commit()
        

    equipment_types = data.pop("Equipment Types", None) # type: list[dict[str, str]]
    
    if equipment_types:
        with DBContext() as session:
            for item in equipment_types:
                name = item["Name"]
                failures = item["Failures"] # type: list[str]

                equipment_type = models.EquipmentType(name=name)
                for failure in failures:
                    failure_obj = session.query(models.EquipmentFailure).filter(models.EquipmentFailure.name == failure).first()
                    equipment_type.add_failure(failure_obj)
                    session.add(equipment_type)

            session.commit()


    equipment = data.pop("Equipment", None) # type: list[dict[str, str]]

    if equipment:
        with DBContext() as session:
            for item in equipment:
                name = item["Name"]
                brand = item["Brand"]
                model = item["Model"]
                serial_number = item["Serial Number"]
                priority_name = item["Priority"]
                year = item["Year"]
                location_name = item["Location"]

                # Optional Items
                capacity = item.pop("Capacity", "")
                code = item.pop("Code", "")
                notes = item.pop("Notes", "")
                type_name = item.pop("Type", None)
                parent_equipment_name = item.pop("Parent Equipment", None)
                acquisition_date = item.pop("Acquisition Date", datetime.now())
                classification1_name = item.pop("Classification 1", None)
                classification2_name = item.pop("Classification 2", None)

                location = session.query(models.Location).filter(models.Location.name == location_name).first()

                if notes:
                    note = models.Note(data=notes)
                    session.add(note)

                equipment_obj = models.Equipment(
                    name=name,
                    capacity=capacity,
                    code=code,
                    note=note if notes else None,
                    brand=brand,
                    model=model,
                    serial_number=serial_number,
                    priority=priority_name,
                    acquisition_date=acquisition_date,
                    location=location,
                    year=year
                )

                if type_name:
                    type_ = session.query(models.EquipmentType).filter(models.EquipmentType.name == type_name).first()
                    equipment_obj.set_type(type_)
                
                if parent_equipment_name:
                    parent_equipment = session.query(models.Equipment).filter(models.Equipment.name == parent_equipment_name).first()
                    equipment_obj.set_parent(parent_equipment)
                
                if classification1_name:
                    classification1 = session.query(models.EquipmentClassification1).filter(models.EquipmentClassification1.name == classification1_name).first()
                    equipment_obj.classification1 = classification1

                if classification2_name:
                    classification2 = session.query(models.EquipmentClassification2).filter(models.EquipmentClassification2.name == classification2_name).first()
                    equipment_obj.classification2 = classification2

                session.add(equipment_obj)
        
            session.commit()


default_user = {
    "first_name": "Admin",
    "last_name": "User",
    "username": "admin",
    "password": "admin"
}

cause_of_failures = [
    "Accidents",
    "Facilities Related",
    "Failure or Premature Wear of Parts (Quality of Parts)",
    "Improper Installation of Replacement Parts",
    "Improper Use of Equipment",
    "Lack of Routine Maintenance Either Preventative or Predictive",
    "Natural Failure of Parts by Use or Aging",
    "Severe Environmental Conditions (Corrosion, Dust, Etc.)",
    "Use of Unsuitable or Poor Quality Replacement Parts"
]

equipment_failures = [
    "Air Leaks",
    "Alignment",
    "Axis Alignaments",
    "Back Fire",
    "Bad Water Quality",
    "Battery",
    "Bearing",
    "Bearing Failure",
    "Bearings",
    "Belts and Pulleys Alignment",
    "Belts Warn Out",
    "Breakdown of Insulating Materials",
    "Broken, Chipped, or Worn gear teeth in the gearbox",
    "Cables and Installations",
    "Cavitation",
    "Chipping",
    "Chuck",
    "Clogged Air Filters",
    "Clogged Filters",
    "Cloggeed Drains",
    "Coalitions",
    "Coil Plugging",
    "Coil Grounding",
    "Combustion Ramp to Fast",
    "Connections",
    "Cooling Issues",
    "Corrosion",
    "Corrosive Environment",
    "Cylinders",
    "Dirty Air/Oil Separator",
    "Dirty Condenser Coils",
    "Drive Train Issues",
    "Drive Diameter",
    "Edge Alignament",
    "Electrical",
    "Environmental Conditions",
    "Erosion",
    "Exceeded Pressure Limits",
    "Excessive Harmonics",
    "Fan (Vibration/Unbalance)",
    "Fan Problems",
    "Faulty Airend",
    "Feed",
    "Flame Scanner",
    "Fouling",
    "Frozen Evaporator Coils",
    "Galling",
    "Gearbox",
    "Generator",
    "Hardware Drivers",
    "Hose",
    "Imbalance",
    "Improperly Greased Motor Bearings",
    "Improper Combustion Ratio",
    "Improper Air-Fuel Ratio",
    "Ingestion of Foreign Matter",
    "Internal Flashover Above Oil",
    "Interturn Faults",
    "Lack of Cleanliness",
    "Lack of Gas",
    "Leak",
    "Lightning and Voltage Transients",
    "Loose Connections",
    "Low Refrigerant",
    "Lubrication",
    "Main Memory",
    "Mechanical",
    "Misalignment",
    "Mother Board",
    "Network Card",
    "Operating System",
    "Operation Outside of The Performance Limits",
    "Overheating",
    "Overloading",
    "Phase Loss",
    "Power Supply",
    "Pressure Level",
    "Pressure Pulsation",
    "Pressure Regulator",
    "Pump",
    "Pumps",
    "Radial and Axial Thrust",
    "Recirculation",
    "Rings",
    "Rotation Axis",
    "Rotor Locked",
    "Seal Failure",
    "Seals",
    "Shaft Seizure or Break",
    "Sharp Edges",
    "Short Circuit",
    "Slow Speed",
    "Strainer Dirty",
    "Superheater",
    "Switchboard",
    "Switchgear",
    "System Breaches",
    "Thermal Stress Fatigue",
    "Thermostate Problems",
    "Tires",
    "Transformers",
    "Trapped Air",
    "Unbalance",
    "Vibration",
    "Vibrations",
    "Winding",
    "Wrong Rotation"
]

equipment_types = [
        {
            "name": "Air Conditioner",
            "failures": [
                "Clogged Air Filters",
                "Cloggeed Drains",
                "Dirty Condenser Coils",
                "Fan (Vibration/Unbalance)",
                "Fan Problems",
                "Frozen Evaporator Coils",
                "Lack of Cleanliness",
                "Loose Connections",
                "Low Refrigerant",
                "Phase Loss",
                "Power Supply"
            ]
        },
        {
            "name": "Air Fan",
            "failures": [
                "Alignment",
                "Bearing Failure",
                "Belts and Pulleys Alignment",
                "Belts Warn Out",
                "Electrical",
                "Excessive Harmonics",
                "Imbalance",
                "Improperly Greased Motor Bearings",
                "Loose Connections",
                "Overheating",
                "Shaft Seizure or Break",
                "Slow Speed",
                "Wrong Rotation"
            ]
        },
        {
            "name": "Blower",
            "failures": [
                "Alignment",
                "Bearing Failure",
                "Belts and Pulleys Alignment",
                "Belts Warn Out",
                "Connections",
                "Electrical",
                "Environmental Conditions",
                "Imbalance",
                "Improperly Greased Motor Bearings",
                "Ingestion of Foreign Matter",
                "Lack of Cleanliness",
                "Loose Connections",
                "Lubrication",
                "Overheating",
                "Overloading",
                "Phase Loss",
                "Rotor Locked",
                "Shaft Seizure or Break",
                "Slow Speed",
                "Wrong Rotation"
            ]
        },
        {
            "name": "Boiler",
            "failures": [
                "Air Leaks",
                "Back Fire",
                "Bad Water Quality",
                "Bearing Failure",
                "Breakdown of Insulating Materials",
                "Combustion Ramp to Fast",
                "Connections",
                "Corrosion",
                "Electrical",
                "Erosion",
                "Fan (Vibration/Unbalance)",
                "Fan Problems",
                "Fouling",
                "Improper Combustion Ratio",
                "Improper Air-Fuel Ratio",
                "Lack of Gas",
                "Leak",
                "Loose Connections",
                "Operation Outside of The Performance Limits",
                "Pressure Level",
                "Pressure Pulsation",
                "Pressure Regulator",
                "Strainer Dirty",
                "Superheater",
                "Thermal Stress Fatigue"
            ]
        },
        {
            "name": "Air Compressor",
            "failures": [
                "Air Leaks",
                "Bearing Failure",
                "Belts and Pulleys Alignment",
                "Belts Warn Out",
                "Clogged Air Filters",
                "Cloggeed Drains",
                "Cooling Issues",
                "Dirty Air/Oil Separator",
                "Drive Train Issues",
                "Electrical",
                "Exceeded Pressure Limits",
                "Galling",
                "Hose",
                "Imbalance",
                "Improperly Greased Motor Bearings",
                "Loose Connections",
                "Lubrication",
                "Mechanical",
                "Overheating",
                "Overloading",
                "Phase Loss",
                "Pressure Regulator",
                "Seal Failure",
                "Shaft Seizure or Break",
                "Slow Speed"
            ]
        },
        {
            "name": "Computer",
            "failures": [
                "Hardware Drivers",
                "Main Memory",
                "Mother Board",
                "Network Card",
                "Operating System",
                "Power Supply"
            ]
        },
        {
            "name": "Concret Mixer",
            "failures": [
                "Axis Alignaments",
                "Bearing Failure",
                "Belts and Pulleys Alignment",
                "Belts Warn Out",
                "Broken, Chipped, or Worn gear teeth in the gearbox",
                "Overloading",
                "Slow Speed",
                "Trapped Air"
            ]
        },
        {
            "name": "Cooling Tower",
            "failures": [
                "Bearing Failure",
                "Broken, Chipped, or Worn gear teeth in the gearbox",
                "Fan (Vibration/Unbalance)",
                "Gearbox",
                "Imbalance",
                "Misalignment"
            ]
        },
        {
            "name": "Die Casting",
            "failures": [
                "Erosion",
                "Sharp Edges",
                "Thermal Stress Fatigue"
            ]
        },
        {
            "name": "Electrical Motor",
            "failures": [
                "Alignment",
                "Bearing Failure",
                "Environmental Conditions",
                "Improperly Greased Motor Bearings",
                "Loose Connections",
                "Shaft Seizure or Break",
                "Switchboard",
                "Winding"
            ]
        },
        {
            "name": "Electrical Substation",
            "failures": [
                "Breakdown of Insulating Materials",
                "Cables and Installations",
                "Connections",
                "Corrosion",
                "Environmental Conditions",
                "Lightning and Voltage Transients",
                "Loose Connections",
                "Mechanical",
                "Overheating",
                "Overloading",
                "Phase Loss",
                "Switchgear",
                "Transformers"
            ]
        },
        {
            "name": "Electrical Transformer",
            "failures": [
                "Breakdown of Insulating Materials",
                "Cooling Issues",
                "Corrosion",
                "Excessive Harmonics",
                "Loose Connections",
                "Operation Outside of The Performance Limits",
                "Overheating",
                "Overloading",
                "Phase Loss",
                "Thermal Stress Fatigue",
                "Unbalance"
            ]
        },
        {
            "name": "Elevator",
            "failures": [
                "Belts and Pulleys Alignment",
                "Belts Warn Out",
                "Broken, Chipped, or Worn gear teeth in the gearbox",
                "Cooling Issues",
                "Corrosion",
                "Electrical",
                "Improperly Greased Motor Bearings",
                "Loose Connections",
                "Lubrication",
                "Mechanical",
                "Overheating",
                "Overloading",
                "Short Circuit",
                "Slow Speed"
            ]
        },
        {
            "name": "HVAC",
            "failures": [
                "Bearing Failure",
                "Belts and Pulleys Alignment",
                "Belts Warn Out",
                "Clogged Air Filters",
                "Cloggeed Drains",
                "Dirty Condenser Coils",
                "Electrical",
                "Fan (Vibration/Unbalance)",
                "Frozen Evaporator Coils",
                "Ingestion of Foreign Matter",
                "Lack of Cleanliness",
                "Lack of Gas",
                "Loose Connections",
                "Low Refrigerant",
                "Phase Loss",
                "Short Circuit",
                "Slow Speed"
            ]
        },
        {
            "name": "Hydraulic Press",
            "failures": [
                "Electrical",
                "Leak",
                "Mechanical",
                "Pumps",
                "System Breaches"
            ]
        },
        {
            "name": "Machinery Tool",
            "failures": [
                "Bearing Failure",
                "Bearings",
                "Drive Diameter",
                "Electrical",
                "Mechanical"
            ]
        },
        {
            "name": "Milling Machine",
            "failures": [
                "Chuck",
                "Feed",
                "Galling",
                "Gearbox",
                "Hose",
                "Pump",
                "Seals"
            ]
        },
        {
            "name": "Fluid Pumping Equipment",
            "failures": [
                "Cavitation",
                "Corrosion",
                "Fouling"
            ]
        },
        {
            "name": "Pump",
            "failures": [
                "Bearing Failure",
                "Cavitation",
                "Clogged Filters",
                "Connections",
                "Erosion",
                "Pressure Pulsation",
                "Radial and Axial Thrust",
                "Recirculation",
                "Seal Failure",
                "Shaft Seizure or Break",
                "Vibrations"
            ]
        },
        {
            "name": "Vehicle",
            "failures": [
                "Back Fire",
                "Battery",
                "Clogged Filters",
                "Generator",
                "Tires"
            ]
        }
    ]