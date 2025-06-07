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

def run_jsonrpc_server():
    """运行 JSONRPC 服务器"""
    logger.info(f"Starting JSONRPC server on {config.JSONRPC_HOST}:{config.JSONRPC_PORT}")
    uvicorn.run(
        jsonrpc_app,
        host=config.JSONRPC_HOST,
        port=config.JSONRPC_PORT,
        log_level=config.LOG_LEVEL.lower(),
        reload=False,
        workers=1,
        timeout_keep_alive=30
    )

def run_chat_server():
    """运行聊天服务器"""
    logger.info(f"Starting Chat server on {config.CHAT_HOST}:{config.CHAT_PORT}")
    uvicorn.run(
        chat_app,
        host=config.CHAT_HOST,
        port=config.CHAT_PORT,
        log_level=config.LOG_LEVEL.lower(),
        reload=False,
        workers=1,
        timeout_keep_alive=30
    )

if __name__ == "__main__":
    import multiprocessing
    
    logger.info(f"Environment: {config.ENV}")
    logger.info(f"Debug mode: {config.DEBUG}")
    
    # 使用多进程而不是异步任务
    jsonrpc_process = multiprocessing.Process(target=run_jsonrpc_server)
    chat_process = multiprocessing.Process(target=run_chat_server)
    
    try:
        # 启动进程
        jsonrpc_process.start()
        chat_process.start()
        
        # 等待进程结束
        jsonrpc_process.join()
        chat_process.join()
    except KeyboardInterrupt:
        logger.info("Shutting down servers...")
        jsonrpc_process.terminate()
        chat_process.terminate()
    except Exception as e:
        logger.error(f"Error running servers: {str(e)}")
        jsonrpc_process.terminate()
        chat_process.terminate()