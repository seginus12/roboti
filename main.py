from fastapi import FastAPI
from router import router
from websocket_manager import ws_connection_manager
import uvicorn
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await ws_connection_manager.cleanup()


# Создаем FastAPI приложение с lifespan управлением
app = FastAPI(
    title="App",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router, prefix="/api", tags=["api"])


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "aahahhahahaha",
        "docs": "/docs",
        "redoc": "/redoc"
    }

