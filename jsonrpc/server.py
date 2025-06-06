from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jsonrpc.routes import model_router, portfolio_router, websocket_router
from jsonrpc.db import init_mongodb, close_mongodb, check_mongodb_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 应用的生命周期管理"""
    try:
        # 启动时初始化 MongoDB 连接
        if not init_mongodb():
            raise HTTPException(status_code=503, detail="Database connection failed")
        yield
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        raise
    finally:
        # 关闭时清理连接
        close_mongodb()

# 创建 FastAPI 应用
fastapi_app = FastAPI(
    title="Portfolio Mind API",
    description="Portfolio Mind API for investment recommendations",
    version="1.0.0",
    lifespan=lifespan
)

# 添加 CORS 中间件
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
fastapi_app.include_router(model_router)
fastapi_app.include_router(portfolio_router)
fastapi_app.include_router(websocket_router)

# 健康检查端点
@fastapi_app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        if check_mongodb_connection():
            return {"status": "healthy", "database": "connected"}
        return {"status": "unhealthy", "database": "disconnected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

# 导出 FastAPI 应用
app = fastapi_app
