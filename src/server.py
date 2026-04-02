from fastapi import APIRouter, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import psutil
import os

from config import AppEnvironment, settings
from handlers import start_exception_handlers
from lifespan import lifespan
from utils.schema import BaseValidationResponse
from apps.user import user_router, protected_user_router


def root_health_path(_app: FastAPI) -> None:
    @_app.get("/", include_in_schema=False)
    def root() -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "SUCCESS"})

    @_app.get("/healthcheck", include_in_schema=False)
    def healthcheck() -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "SUCCESS"})


def init_middlewares(_app: FastAPI) -> None:
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def create_app(debug: bool = False) -> FastAPI:
    _app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc" if debug else None,
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,
            "displayRequestDuration": True,
            "tryItOutEnabled": True,
            "requestSnippetsEnabled": True,
            "withCredentials": True,
            "persistAuthorization": True,
        },
        lifespan=lifespan,
    )

    root_health_path(_app)

    base_router = APIRouter()
    base_router.include_router(user_router)
    base_router.include_router(protected_user_router)
    _app.include_router(base_router, responses={422: {"model": BaseValidationResponse}})

    init_middlewares(_app)    
    start_exception_handlers(_app)

    return _app
