import asyncio
import pytest
from fastmcp import FastMCP
from cryptomcp.server.main import analyze_portfolio, analyze_portfolio_stream

@pytest.mark.asyncio
async def test_analyze_portfolio():
    # 测试一次性分析
    result = await analyze_portfolio(
        symbols=["BTC", "ETH"],
        show_reasoning=True
    )
    assert isinstance(result, dict)
    assert "success" in result
    if result["success"]:
        assert "data" in result
    else:
        assert "error" in result

@pytest.mark.asyncio
async def test_analyze_portfolio_stream():
    # 测试流式分析
    async for update in analyze_portfolio_stream(
        symbols=["BTC", "ETH"],
        show_reasoning=True
    ):
        assert isinstance(update, dict)
        assert "type" in update
        if update["type"] == "result":
            assert "data" in update
        elif update["type"] == "error":
            assert "error" in update["data"]

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_analyze_portfolio())
    asyncio.run(test_analyze_portfolio_stream()) 