from .urls import router as user_router
from .urls import protected_router as protected_user_router

__all__ = ["user_router", "protected_user_router"]
