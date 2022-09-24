from enum import Enum as PythonEnum


class Priority(PythonEnum):
    NA = "NA"
    Low = "Low"
    Medium = "Medium"
    High = "High"


class Impact(PythonEnum):
    Low = "Low Impact"
    Medium = "Medium Impact"
    High = "High Impact"


class MaintenancePlanRegimen(PythonEnum):
    DATE = "Date"
    READING = "Reading"
    MIXED = "Mixed"


class WOStatus(PythonEnum):
    Open = "Open"
    Closed = "Closed"
    Closed_Early = "Closed Early"


class MaintenanceActivityRegimen(PythonEnum):
    DAYS = "day(s)"
    WEEKS = "week(s)"
    MONTHS = "month(s)"
    YEARS = "year(s)"


class WorkType(PythonEnum):
    Corrective = "Corrective"
    Preventive = "Preventive"
    Predictive = "Predictive"
    Support = "Support"
    Improvement = "Improvement"
    Other = "Other"


class Condition(PythonEnum):
    Good = "Good"
    Fair = "Fair"
    Bad = "Bad"