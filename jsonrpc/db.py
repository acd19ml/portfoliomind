from fastapi import HTTPException
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
import sys
import os

# 将项目根目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config

# 配置日志
logger = logging.getLogger(__name__)

# MongoDB 连接
mongo_client = None
mongo_db = None

def init_mongodb():
    """初始化 MongoDB 连接"""
    global mongo_client, mongo_db
    try:
        mongo_client = MongoClient(
            config.MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            retryWrites=True,
            retryReads=True
        )
        
        # 测试连接
        mongo_client.admin.command('ping')
        mongo_db = mongo_client[config.MONGODB_DB]
        logger.info(f"MongoDB connected successfully to {config.MONGODB_DB}")
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        return False

def close_mongodb():
    """关闭 MongoDB 连接"""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed")

def get_mongo_db():
    """获取 MongoDB 数据库连接"""
    if not mongo_db:
        raise HTTPException(status_code=503, detail="Database not connected")
    return mongo_db

def check_mongodb_connection():
    """检查 MongoDB 连接状态"""
    try:
        if mongo_client:
            mongo_client.admin.command('ping')
            return True
        return False
    except Exception as e:
        logger.error(f"MongoDB connection check failed: {str(e)}")
        return False 