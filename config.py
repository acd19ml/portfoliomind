import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 服务器配置
class Config:
    # JSONRPC 服务器配置
    JSONRPC_HOST = os.getenv("JSONRPC_HOST", "0.0.0.0")
    JSONRPC_PORT = int(os.getenv("JSONRPC_PORT", "8000"))
    
    # 聊天服务器配置
    CHAT_HOST = os.getenv("CHAT_HOST", "0.0.0.0")
    CHAT_PORT = int(os.getenv("CHAT_PORT", "8008"))
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # MongoDB 配置
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB = os.getenv("MONGODB_DB", "portfoliomind")
    
    # 其他配置
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    ENV = os.getenv("ENV", "development")

# 创建配置实例
config = Config() 