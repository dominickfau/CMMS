import logging
from sqlalchemy import create_engine
import cmms
from cmms.config import DATABASE_URL_WITHOUT_SCHEMA, SCHEMA_CREATE_STATEMENT
from cmms.database import engine
from cmms import models
from cmms.api.extensions import app
from cmms.api.routes import auth, equipment, user, equipmenttype, equipmentfailure, causeofequipmentfailure, maintenanceplan, location
from cmms.defaultdata import load_default_data

logger = logging.getLogger("api")


app.include_router(causeofequipmentfailure.router)
app.include_router(equipment.router)
app.include_router(equipmentfailure.router)
app.include_router(equipmenttype.router)
app.include_router(location.router)
app.include_router(maintenanceplan.router)
app.include_router(auth.router)
app.include_router(user.router)


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 100)
    logger.info("[SYSTEM] Starting API server.")

    temp_engine = create_engine(DATABASE_URL_WITHOUT_SCHEMA)
    with temp_engine.begin() as session:
        session.execute(SCHEMA_CREATE_STATEMENT)

    logger.info("[SYSTEM] Creating database tables.")
    models.DeclarativeBase.metadata.create_all(bind=engine)
    load_default_data()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("[SYSTEM] API server shutting down.")


@app.get("/")
def root():
    return {"message": "Hello World."}