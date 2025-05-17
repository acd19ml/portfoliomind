# cryptomcp/client/main.py
import asyncio
import json
import logging
import websockets
import sys
from typing import List, Optional, Dict, Any
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PortfolioAnalysisClient')

# 禁用 websockets 的调试日志
logging.getLogger('websockets').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)

def print_json(data: Dict[str, Any], indent: int = 2):
    """格式化打印 JSON 数据"""
    print(json.dumps(data, indent=indent))

def clear_line():
    """清除当前行"""
    print('\r' + ' ' * 100 + '\r', end='', flush=True)

def print_progress(message: str):
    """打印进度信息"""
    clear_line()
    print(message, end='', flush=True)

class PortfolioAnalysisClient:
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.progress_ws: Optional[websockets.WebSocketClientProtocol] = None
        self.model_ws: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.analysis_id = 0
        self._heartbeat_task = None
        self._stop_heartbeat = False
        
    async def _send_heartbeat(self):
        """发送心跳消息以保持连接活跃"""
        while not self._stop_heartbeat:
            try:
                if self.progress_ws and self.progress_ws.state == websockets.protocol.State.OPEN:
                    await self.progress_ws.send("ping")
                    logger.debug("Sent heartbeat ping")
                await asyncio.sleep(30)  # 每30秒发送一次心跳
            except Exception as e:
                logger.error(f"Heartbeat error: {str(e)}")
                break
        
    async def connect(self) -> bool:
        """连接到 WebSocket 服务器"""
        try:
            # 连接进度更新端点
            progress_url = f"ws://{self.host}:{self.port}/ws/progress"
            self.progress_ws = await websockets.connect(progress_url)
            
            # 等待连接确认
            response = await self.progress_ws.recv()
            data = json.loads(response)
            if data["method"] == "connection.status" and data["params"]["status"] == "connected":
                logger.info("Progress connection confirmed")
            else:
                logger.warning("Unexpected connection response")
            
            # 启动心跳任务
            self._stop_heartbeat = False
            self._heartbeat_task = asyncio.create_task(self._send_heartbeat())
            
            # 连接模型调用端点
            model_url = f"ws://{self.host}:{self.port}/ws/model"
            self.model_ws = await websockets.connect(model_url)
            
            self.connected = True
            logger.info("Connected to server")
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            self.connected = False
            return False
        
    async def analyze_portfolio(self, symbols: List[str], show_reasoning: bool = True) -> Dict[str, Any]:
        """分析投资组合"""
        if not self.connected:
            logger.error("Not connected to server")
            raise ConnectionError("Not connected to server")
            
        self.analysis_id += 1
        current_id = self.analysis_id
        logger.info(f"Starting analysis for {symbols}")
        
        try:
            # 启动进度监听
            progress_task = asyncio.create_task(self._listen_progress(current_id))
            
            # 发送分析请求
            request = {
                "jsonrpc": "2.0",
                "id": current_id,
                "method": "analyzePortfolio",
                "params": {
                    "cryptos": symbols,
                    "show_reasoning": show_reasoning
                }
            }
            await self.model_ws.send(json.dumps(request))
            
            # 等待最终结果
            start_time = datetime.now()
            while True:
                try:
                    response = await asyncio.wait_for(self.model_ws.recv(), timeout=300)
                    data = json.loads(response)
                    
                    if "result" in data:
                        duration = (datetime.now() - start_time).total_seconds()
                        logger.info(f"Analysis completed in {duration:.1f}s")
                        return data["result"]
                    elif "error" in data:
                        logger.error(f"Analysis failed: {data['error']['message']}")
                        raise Exception(data["error"]["message"])
                        
                except asyncio.TimeoutError:
                    logger.error("Analysis timed out after 5 minutes")
                    raise TimeoutError("Analysis timed out")
                    
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            raise
        finally:
            if not progress_task.done():
                progress_task.cancel()
                try:
                    await progress_task
                except asyncio.CancelledError:
                    pass
                
    async def _listen_progress(self, analysis_id: int):
        """监听进度更新"""
        print("\nProgress Updates:")  # 初始化进度显示
        while True:
            try:
                message = await self.progress_ws.recv()
                logger.debug(f"Received progress message: {message}")  # 添加调试日志
                
                # 跳过心跳响应
                if message == "pong":
                    continue
                    
                try:
                    data = json.loads(message)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON message: {message}")
                    continue
                    
                if data.get("method") == "analysis.progress":
                    params = data.get("params", {})
                    if params.get("type") == "status":
                        status = params.get("status", "")
                        crypto = params.get("crypto") or params.get("agent") or "Overall"
                        print(f"{crypto}: {status}")  # 直接打印每个更新
                    elif params.get("type") == "result":
                        print("\nAnalysis Results:")
                        print_json(params.get("data", {}))
                        return  # 收到结果后结束监听
            except websockets.exceptions.ConnectionClosed:
                logger.info("Progress connection closed")
                break
            except Exception as e:
                logger.error(f"Progress error: {str(e)}")
                break
                
    async def close(self):
        """关闭所有连接"""
        self._stop_heartbeat = True
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            
        if self.progress_ws:
            await self.progress_ws.close()
            self.progress_ws = None
        if self.model_ws:
            await self.model_ws.close()
            self.model_ws = None
        self.connected = False
        logger.info("Disconnected from server")

async def main():
    """测试客户端功能"""
    client = PortfolioAnalysisClient()
    try:
        if not await client.connect():
            return
            
        try:
            await client.analyze_portfolio(["BTC", "ETH"])
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())