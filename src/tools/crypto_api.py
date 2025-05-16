import os
import requests
from typing import List
from src.data.crypto_models import CryptoCoin, CryptoCoinResponse
from src.data.crypto_cache import get_crypto_cache

_cache = get_crypto_cache()

def get_coins() -> List[CryptoCoin]:
    """Fetch cryptocurrency data from LunarCrush API.
    
    Returns:
        List[CryptoCoin]: A list of cryptocurrency data objects.
    """
    # Check cache first
    if cached_data := _cache.get_coins():
        return [CryptoCoin(**coin) for coin in cached_data]

    # If not in cache or cache expired, fetch from API
    headers = {}
    if api_key := os.environ.get("LUNARCRUSH_API_KEY"):
        headers["Authorization"] = f"Bearer {api_key}"

    url = "https://lunarcrush.com/api4/public/coins/list/v1"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {response.status_code} - {response.text}")

    # Parse response with Pydantic model
    data = response.json()
    response_model = CryptoCoinResponse(**data)
    coins = response_model.data

    if not coins:
        return []
    
    # Cache the results
    _cache.set_coins([coin.model_dump() for coin in coins])
    
    return coins
