"""测试lifespan是否工作"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Test lifespan"""
    print("=" * 80)
    print("🚀 STARTUP: Lifespan function called!")
    print("=" * 80)
    yield
    print("=" * 80)
    print("🛑 SHUTDOWN: Lifespan shutdown called!")
    print("=" * 80)


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
