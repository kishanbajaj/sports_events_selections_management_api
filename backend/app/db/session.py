import os
import logging

from databases import Database
from fastapi import FastAPI
from app.config.app_config import appConfig

logger = logging.getLogger(__name__)

async def connect_to_db(app: FastAPI) -> None:
    DATABASE_URI: str = f"postgresql://{appConfig.POSTGRES_USER}:{appConfig.POSTGRES_PASSWORD}@{appConfig.POSTGRES_SERVER}:{appConfig.POSTGRES_PORT}/{appConfig.POSTGRES_DB}"
    DATABASE_URI = f"{DATABASE_URI}_test" if os.environ.get("TESTING") else DATABASE_URI

    database = Database(
        DATABASE_URI,
        min_size=appConfig.DB_MIN_CONNECTION_POOL,
        max_size=appConfig.DB_MAX_CONNECTION_POOL,
    )

    try:
        logger.warning("==== CONNECTING TO DB! ====")
        await database.connect()
        app.state._db = database
        logger.warning("==== CONNECTED TO DB! ====")
    except Exception as ex:
        logger.warning("==== CONNECTION ERROR ====")
        logger.warning(ex)


async def close_db_connection(app: FastAPI) -> None:
    try:
        logger.warning("==== DISCONNECTING FROM DB! ====")
        await app.state._db.disconnect()
        logger.warning("==== DISCONNECTED FROM DB! ====")
    except Exception as ex:
        logger.warning("==== DB DISCONNECT ERROR ====")
        logger.warning(ex)