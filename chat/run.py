import uvicorn
import logging
from server import app

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Chat server on 0.0.0.0:8008")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8008,
        log_level="debug",
        reload=False,
        workers=1,
        timeout_keep_alive=30
    )