import os
import pytest
from src.tools.crypto_api import get_coins


def test_get_coins():
    """Test the get_coins function."""
    # Check if API key is set
    if not os.environ.get("LUNARCRUSH_API_KEY"):
        pytest.skip("LUNARCRUSH_API_KEY environment variable not set")

    # Get coins data
    coins = get_coins()
    
    # Basic assertions
    assert coins is not None
    assert len(coins) > 0
    
    # Check first coin (usually Bitcoin)
    first_coin = coins[0]
    assert first_coin.symbol == "BTC"
    assert first_coin.name == "Bitcoin"
    assert first_coin.price > 0
    assert first_coin.market_cap > 0
    
    # Print some basic info for verification
    print(f"\nFound {len(coins)} coins")
    print(f"First coin: {first_coin.name} ({first_coin.symbol})")
    print(f"Price: ${first_coin.price:,.2f}")
    print(f"Market Cap: ${first_coin.market_cap:,.2f}")
    print(f"24h Change: {first_coin.percent_change_24h:,.2f}%") 