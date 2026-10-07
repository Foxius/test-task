from fastapi import FastAPI

from app.api.routes import router


def create_app() -> FastAPI:
    application = FastAPI(title="Payment Processing Service", version="1.0.0")
    application.include_router(router)
    return application


app = create_app()
