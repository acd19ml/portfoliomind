import uvicorn
import logging
from server import app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    # 使用 0.0.0.0 作为主机地址，允许来自任何 IP 的连接
    # 这对于 WSL2 和 Docker 之间的通信是必要的
    uvicorn.run(
        app,
        host="0.0.0.0",  # 允许来自任何 IP 的连接
        port=8000,
        reload=False,    # 禁用热重载以避免潜在的问题
        log_level="info",
        workers=1,       # 使用单个工作进程
        timeout_keep_alive=30  # 增加保持连接超时时间
    ) 