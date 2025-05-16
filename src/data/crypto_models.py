from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from decimal import Decimal


class Blockchain(BaseModel):
    model_config = ConfigDict(extra='ignore')  # 处理数据中存在但 model中没有定义的字段
    
    type: Optional[str] = None  # 处理 model中已定义但数据中缺失的字段
    network: str
    address: Optional[str] = None
    decimals: Optional[int] = None


class Config(BaseModel):
    model_config = ConfigDict(extra='ignore')  # Ignore extra fields
    
    generated: int  # Unix timestamp when the data was generated


class CryptoCoin(BaseModel):
    model_config = ConfigDict(extra='ignore')  # Ignore extra fields
    
    id: int
    symbol: str
    name: str
    price: Decimal
    price_btc: Optional[Decimal] = None
    volume_24h: Optional[Decimal] = None
    volatility: Optional[Decimal] = None
    circulating_supply: Optional[Decimal] = None
    max_supply: Optional[Decimal] = None
    percent_change_1h: Optional[Decimal] = None
    percent_change_24h: Optional[Decimal] = None
    percent_change_7d: Optional[Decimal] = None
    percent_change_30d: Optional[Decimal] = None
    market_cap: Optional[Decimal] = None
    market_cap_rank: Optional[int] = None
    interactions_24h: Optional[int] = None
    social_volume_24h: Optional[int] = None
    social_dominance: Optional[Decimal] = None
    market_dominance: Optional[Decimal] = None
    market_dominance_prev: Optional[Decimal] = None
    galaxy_score: Optional[float] = None
    galaxy_score_previous: Optional[float] = None
    alt_rank: Optional[int] = None
    alt_rank_previous: Optional[int] = None
    sentiment: Optional[int] = None
    categories: Optional[str] = None
    blockchains: Optional[List[Blockchain]] = None
    last_updated_price: Optional[int] = None
    last_updated_price_by: Optional[str] = None
    topic: Optional[str] = None
    logo: Optional[str] = None


class CryptoCoinResponse(BaseModel):
    model_config = ConfigDict(extra='ignore')  # Ignore extra fields
    
    config: Config
    data: List[CryptoCoin]
