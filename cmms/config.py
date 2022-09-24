from __future__ import annotations
import os
import logging
import secrets
from typing import Any
from dataclasses import dataclass
from PyQt5.QtCore import QSettings


@dataclass
class DefaultSetting:
    """Default settings."""

    settings: QSettings
    name: str
    value: str
    group_name: str = None

    @property
    def hive_location(self) -> str:
        """Return the hive location path for this setting."""
        base = f"HKEY_CURRENT_USER\SOFTWARE\{COMPANY_NAME}\{PROGRAM_NAME}"
        if self.group_name:
            base += f"\{self.group_name}"
        return f"{base}\{self.name}"

    def initialize_setting(self) -> DefaultSetting:
        """Initialize the default setting or pulls the current setting value."""
        if self.group_name:
            self.settings.beginGroup(self.group_name)

        if not self.settings.contains(self.name):
            self.settings.setValue(self.name, self.value)
        else:
            self.value = self.settings.value(self.name)

        if self.group_name:
            self.settings.endGroup()
        return self

    def save(self) -> DefaultSetting:
        """Save the default setting."""
        if self.group_name:
            self.settings.beginGroup(self.group_name)

        self.settings.setValue(self.name, self.value)

        if self.group_name:
            self.settings.endGroup()
        return self



COMPANY_NAME = "DF-Software"
PROGRAM_NAME = "CMMS"
PROGRAM_VERSION = "0.0.1"
USER_HOME_FOLDER = os.path.expanduser("~")
COMPANY_FOLDER = os.path.join(USER_HOME_FOLDER, "Documents", COMPANY_NAME)
PROGRAM_FOLDER = os.path.join(COMPANY_FOLDER, PROGRAM_NAME)
LOG_FOLDER = os.path.join(PROGRAM_FOLDER, "Logs")
DATABASE_FOLDER = os.path.join(PROGRAM_FOLDER, "Database")
TEMP_DATA_FOLDER = os.path.join(PROGRAM_FOLDER, "Temp Data")
ENCODING_STR = "utf-8"


if not os.path.exists(COMPANY_FOLDER):
    os.mkdir(COMPANY_FOLDER)

if not os.path.exists(PROGRAM_FOLDER):
    os.mkdir(PROGRAM_FOLDER)

if not os.path.exists(LOG_FOLDER):
    os.mkdir(LOG_FOLDER)

if not os.path.exists(DATABASE_FOLDER):
    os.mkdir(DATABASE_FOLDER)

if not os.path.exists(TEMP_DATA_FOLDER):
    os.mkdir(TEMP_DATA_FOLDER)


settings = QSettings(COMPANY_NAME, PROGRAM_NAME)

# Program settings
DATETIME_FORMAT = "%m-%d-%Y %H:%M"
DATE_FORMAT = "%m-%d-%Y"
DEFAULT_DUE_DATE_PUSH_BACK_DAYS = 30
SECRET_KEY = DefaultSetting(settings=settings, name="Secret Key", value=secrets.token_hex(32)).initialize_setting().value
LOGIN_TOKEN_EXPIRE_MINUTES = DefaultSetting(settings=settings, name="Login Token Expire Minutes", value=60).initialize_setting().value

DEBUG = DefaultSetting(settings=settings, name="debug", value=False).initialize_setting().value
if DEBUG == "true":
    DEBUG = True
else:
    DEBUG = False


# Logging settings
LOG_FILE = "CMMS.log"
SQLALCHEMY_ENGINE_LOG_FILE = "SQLAlchemy Engine.log"
SQLALCHEMY_POOL_LOG_FILE = "SQLAlchemy Pool.log"
SQLALCHEMY_DIALECT_LOG_FILE = "SQLAlchemy Dialect.log"
SQLALCHEMY_ORM_LOG_FILE = "SQLAlchemy ORM.log"

MAX_LOG_SIZE_MB = DefaultSetting(settings=settings, group_name="Logging", name="max_log_size_mb", value=5).initialize_setting().value
MAX_LOG_COUNT = DefaultSetting(settings=settings, group_name="Logging", name="max_log_count", value=3).initialize_setting().value
LOG_LEVEL = logging.DEBUG # DefaultSetting(settings=settings, group_name="Logging", name="log_level", value=logging.INFO).initialize_setting().value
if DEBUG:
    LOG_LEVEL = logging.DEBUG


# Database Settings
SCHEMA_NAME = DefaultSetting(settings=settings, group_name="Database/MySQL", name="Schema Name", value=f"{PROGRAM_NAME.lower().replace(' ', '')}").initialize_setting().value
DATABASE_USER = DefaultSetting(settings=settings, group_name="Database/MySQL", name="User", value="").initialize_setting().value
DATABASE_PASSWORD = DefaultSetting(settings=settings, group_name="Database/MySQL", name="Password", value="").initialize_setting().value
DATABASE_HOST = DefaultSetting(settings=settings, group_name="Database/MySQL", name="Host", value="localhost").initialize_setting().value
DATABASE_PORT = DefaultSetting(settings=settings, group_name="Database/MySQL", name="Port", value="3306").initialize_setting().value
DATABASE_DUMP_LOCATION = DefaultSetting(settings=settings, group_name="Database/MySQL", name="MySQLDump Location", value="").initialize_setting().value

SCHEMA_CREATE_STATEMENT = f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME} DEFAULT CHARACTER SET utf8 COLLATE utf8_bin ;"
DATABASE_URL_WITHOUT_SCHEMA = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}"
DATABASE_URL_WITH_SCHEMA = f"{DATABASE_URL_WITHOUT_SCHEMA}/{SCHEMA_NAME}"
FORCE_REBUILD_DATABASE = DefaultSetting(settings=settings, group_name="Database", name="force_rebuild_database", value=False,).initialize_setting().value
if FORCE_REBUILD_DATABASE == "true":
    FORCE_REBUILD_DATABASE = True
else:
    FORCE_REBUILD_DATABASE = False


# Fishbowl settings
FISHBOWL_SCHEMA_NAME = DefaultSetting(settings=settings, group_name="Database/Fishbowl", name="Schema Name", value="").initialize_setting().value
FISHBOWL_DATABASE_USER = DefaultSetting(settings=settings, group_name="Database/Fishbowl", name="User", value="gone").initialize_setting().value
FISHBOWL_DATABASE_PASSWORD = DefaultSetting(settings=settings, group_name="Database/Fishbowl", name="Password", value="fishing").initialize_setting().value
FISHBOWL_DATABASE_HOST = DefaultSetting(settings=settings, group_name="Database/Fishbowl", name="Host", value="").initialize_setting().value
FISHBOWL_DATABASE_PORT = DefaultSetting(settings=settings, group_name="Database/Fishbowl", name="Port", value="3305").initialize_setting().value
FISHBOWL_DATABASE_URL = f"mysql+pymysql://{FISHBOWL_DATABASE_USER}:{FISHBOWL_DATABASE_PASSWORD}@{FISHBOWL_DATABASE_HOST}:{FISHBOWL_DATABASE_PORT}/{FISHBOWL_SCHEMA_NAME}"

# Github settings
GITHUB_USERNAME = "dominickfau"
GITHUB_REPO_NAME = "CMMS"
GITHUB_LATEST_RELEASE_ENDPOINT = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO_NAME}/releases/latest"