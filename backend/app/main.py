from fastapi import FastAPI
from app.config.app_config import appConfig
from app.db.session import close_db_connection, connect_to_db
from app.api_routes.api import api_router

def application():
    app = FastAPI()

    @app.on_event("startup")
    async def startup() -> None:
        await connect_to_db(app)

    @app.on_event("shutdown")
    async def shutdown():
        await close_db_connection(app)

    app.include_router(api_router, prefix=appConfig.API_STR)
    return app

app = application()