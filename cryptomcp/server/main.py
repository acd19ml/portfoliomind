# cryptomcp/server/main.py
from typing import Any, List, Dict
import json
import websockets
import logging
import sys

from fastmcp import FastMCP

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="PortfolioMind",
    instructions="""
    This server provides cryptocurrency portfolio analysis tools.
    Use analyze_portfolio() for one-time analysis.
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
        logger.debug(f"Starting portfolio analysis for symbols: {symbols}")
        
        # 连接到模型调用 WebSocket
        uri = "ws://localhost:8000/ws/model"
        logger.debug(f"Connecting to WebSocket at {uri}")
        
        try:
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
                logger.debug(f"Sending request: {request}")
                await websocket.send(json.dumps(request))

                # 等待最终结果
                while True:
                    response = await websocket.recv()
                    data = json.loads(response)
                    logger.debug(f"Received response: {data}")
                    
                    if "result" in data:
                        return {"success": True, "data": data["result"]}
                    elif "error" in data:
                        return {"success": False, "error": data["error"]["message"]}
        except websockets.exceptions.ConnectionRefused:
            logger.error("Failed to connect to WebSocket server")
            return {"success": False, "error": "Model server is not running"}
        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket error: {str(e)}")
            return {"success": False, "error": f"WebSocket error: {str(e)}"}

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    logger.info("Starting PortfolioMind server...")
    try:
        mcp.run(
            transport="streamable-http",
            path="/mcp",
            host="127.0.0.1",
            port=9000,
            log_level="debug"  # 使用 debug 级别以获取更多日志信息
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        sys.exit(1)
