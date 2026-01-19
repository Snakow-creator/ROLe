from fastapi import APIRouter
from routers import root
from api.auth.handler import router as auth_router
from tasks.handler import router as tasks_router
from items.handler import router as items_router
from users.handler import router as users_router

# create init routers
init_router = APIRouter()

# include routers
init_router.include_router(root.router)
init_router.include_router(auth_router)
init_router.include_router(tasks_router)
init_router.include_router(items_router)
init_router.include_router(users_router)
