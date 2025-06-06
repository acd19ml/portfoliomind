import asyncio
import uvicorn
import logging
from jsonrpc.server import app as jsonrpc_app
from chat.server import app as chat_app
from config import config

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_jsonrpc_server():
    """运行 JSONRPC 服务器"""
    config_uvicorn = uvicorn.Config(
        jsonrpc_app,
        host=config.JSONRPC_HOST,
        port=config.JSONRPC_PORT,
        log_level=config.LOG_LEVEL.lower(),
        reload=config.DEBUG
    )
    server = uvicorn.Server(config_uvicorn)
    await server.serve()

async def run_chat_server():
    """运行聊天服务器"""
    config_uvicorn = uvicorn.Config(
        chat_app,
        host=config.CHAT_HOST,
        port=config.CHAT_PORT,
        log_level=config.LOG_LEVEL.lower(),
        reload=config.DEBUG
    )
    server = uvicorn.Server(config_uvicorn)
    await server.serve()

async def run_all_servers():
    """同时运行所有服务器"""
    logger.info(f"Starting JSONRPC server on {config.JSONRPC_HOST}:{config.JSONRPC_PORT}")
    logger.info(f"Starting Chat server on {config.CHAT_HOST}:{config.CHAT_PORT}")
    logger.info(f"Environment: {config.ENV}")
    logger.info(f"Debug mode: {config.DEBUG}")
    
    # 创建任务
    jsonrpc_task = asyncio.create_task(run_jsonrpc_server())
    chat_task = asyncio.create_task(run_chat_server())
    
    # 等待所有服务器运行
    await asyncio.gather(jsonrpc_task, chat_task)

if __name__ == "__main__":
    try:
        asyncio.run(run_all_servers())
    except KeyboardInterrupt:
        logger.info("Shutting down servers...")
    except Exception as e:
        logger.error(f"Error running servers: {str(e)}") 