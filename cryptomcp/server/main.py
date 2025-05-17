# server.py
from typing import Any, List, Dict, AsyncGenerator
import asyncio
import json
import websockets

from fastmcp import FastMCP
from src.main import run_portfoliomind

mcp = FastMCP(
    name="PortfolioMind",
    instructions="""
    This server provides cryptocurrency portfolio analysis tools.
    Use analyze_portfolio() for one-time analysis.
    Use analyze_portfolio_stream() for real-time analysis with status updates.
    """,
    cors_origins=["*"],  # 允许所有来源的请求
    auth_required=False  # 暂时禁用认证
)

DEFAULT_MODEL = "gpt-4o"
DEFAULT_PROVIDER = "OpenAI"

@mcp.tool()
async def analyze_portfolio(
    symbols: List[str],
    model_name: str = DEFAULT_MODEL,
    model_provider: str = DEFAULT_PROVIDER,
    show_reasoning: bool = True
) -> Dict[str, Any]:
    """一次性分析接口，直接返回完整结果。"""
    try:
        # 连接到模型调用 WebSocket
        uri = "ws://localhost:8000/ws/model"
        async with websockets.connect(uri) as websocket:
            # 发送分析请求
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "analyzePortfolio",
                "params": {
                    "cryptos": symbols,
                    "show_reasoning": show_reasoning
                }
            }
            await websocket.send(json.dumps(request))

            # 等待最终结果
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                
                if "result" in data:
                    return {"success": True, "data": data["result"]}
                elif "error" in data:
                    return {"success": False, "error": data["error"]["message"]}

    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
async def analyze_portfolio_stream(
    symbols: List[str],
    model_name: str = DEFAULT_MODEL,
    model_provider: str = DEFAULT_PROVIDER,
    show_reasoning: bool = True
) -> AsyncGenerator[Dict[str, Any], None]:
    """实时流式分析接口，返回进度更新和最终结果。"""
    try:
        # 连接到模型调用 WebSocket
        uri = "ws://localhost:8000/ws/model"
        async with websockets.connect(uri) as websocket:
            # 发送分析请求
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "analyzePortfolio",
                "params": {
                    "cryptos": symbols,
                    "show_reasoning": show_reasoning
                }
            }
            await websocket.send(json.dumps(request))

            # 接收所有更新
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                
                if "method" in data and data["method"] == "analysis.progress":
                    # 处理进度更新
                    yield data["params"]
                elif "result" in data:
                    # 处理最终结果
                    yield {"type": "result", "data": data["result"]}
                    break
                elif "error" in data:
                    # 处理错误
                    yield {"type": "error", "data": {"error": data["error"]["message"]}}
                    break

    except Exception as e:
        yield {"type": "error", "data": {"error": str(e)}}

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        path="/mcp",
        host="127.0.0.1",
        port=9000,
        log_level="debug"  # 使用 debug 级别以获取更多日志信息
    )
