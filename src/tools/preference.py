from typing import Dict
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
import os
from dotenv import load_dotenv
import json

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB 配置
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://34.133.224.209:27017/")
MONGODB_USER = os.getenv("MONGODB_USER", "admin")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD", "admin")
DB_NAME = os.getenv("MONGODB_DB", "portfoliomind")

def get_user_preference(address: str) -> Dict:
    """获取用户投资偏好
    
    Args:
        address: 用户地址
        
    Returns:
        dict: 包含以下字段的用户偏好
            - duration_days: 投资期限（天）
            - return_rate: 目标收益率
            - min_investment: 最小投资金额（美元）
            - max_investment: 最大投资金额（美元）
            - tokens_number: 最大代币数量
    """
    client = None
    
    try:
        # 创建 MongoDB 连接
        client = MongoClient(
            MONGODB_URL,
            username=MONGODB_USER,
            password=MONGODB_PASSWORD,
            serverSelectionTimeoutMS=5000,
            retryWrites=True,
            retryReads=True
        )
        
        # 测试连接
        client.admin.command('ping')
        logger.info("MongoDB connected successfully")
        
        # 获取数据库和集合
        db = client[DB_NAME]
        users_collection = db['users']
        
        # 查找用户
        user = users_collection.find_one({"_id": address})
        if not user:
            logger.warning(f"User with address {address} not found")
            return get_default_preference()
            
        # 记录原始用户数据
        logger.info(f"Raw user data from MongoDB: {json.dumps(user, default=str)}")
            
        # 获取偏好
        preference = user.get('personal_preference', {})
        if not preference:
            logger.warning(f"No preferences found for user {address}")
            return get_default_preference()
            
        # 记录原始偏好数据
        logger.info(f"Raw preference data: {json.dumps(preference, default=str)}")
        
        # 检查必要字段是否存在且类型正确
        required_fields = {
            'duration_days': int,
            'return_rate': float,
            'min_investment': float,
            'max_investment': float,
            'tokens_number': float
        }
        
        # 尝试转换所有字段，如果任何字段转换失败，返回默认值
        try:
            converted_preference = {
                field: type_converter(preference.get(field))
                for field, type_converter in required_fields.items()
            }
            # 记录转换后的数据
            logger.info(f"Converted preference data: {json.dumps(converted_preference, default=str)}")
            return converted_preference
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid preference data for user {address}, error: {str(e)}, using default values")
            return get_default_preference()
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        return get_default_preference()
    except Exception as e:
        logger.error(f"Error getting user preference: {str(e)}")
        return get_default_preference()
    finally:
        # 关闭连接
        if client:
            try:
                client.close()
                logger.info("MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {str(e)}")

def get_default_preference() -> Dict:
    """返回默认的用户偏好"""
    return {
        "duration_days": 30,  # 默认30天
        "return_rate": 10.0,  # 默认10%收益率
        "min_investment": 100.0,  # 默认最小投资100美元
        "max_investment": 1000.0,  # 默认最大投资1000美元
        "tokens_number": 100  # 默认最多100个代币
    }
