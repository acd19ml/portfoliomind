from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
import sys
import os
import asyncio
from typing import Dict, Set
from starlette.websockets import WebSocketState

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import run_portfoliomind
from src.utils.analysts import ANALYST_ORDER
from src.llm.models import LLM_ORDER, get_model_info

# 创建 FastAPI 应用
fastapi_app = FastAPI()

# 存储活跃的进度订阅者
progress_subscribers: Set[WebSocket] = set()

async def safe_close_websocket(websocket: WebSocket):
    """安全地关闭 WebSocket 连接"""
    if websocket.client_state != WebSocketState.DISCONNECTED:
        try:
            await websocket.close()
        except Exception:
            pass

@fastapi_app.websocket("/ws/progress")
async def ws_progress(websocket: WebSocket):
    """处理进度更新的 WebSocket 端点"""
    await websocket.accept()
    progress_subscribers.add(websocket)
    print("Progress subscriber connected")

    try:
        # 发送初始连接确认
        await websocket.send_text(json.dumps({
            "jsonrpc": "2.0",
            "method": "connection.status",
            "params": {"status": "connected"}
        }))

        # 保持连接活跃，等待进度更新
        while True:
            try:
                # 设置较短的超时时间，以便能够及时响应断开连接
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                # 如果收到心跳消息，发送响应
                if data == "ping":
                    await websocket.send_text("pong")
                    print("Received ping, sent pong")
            except asyncio.TimeoutError:
                # 超时是正常的，继续等待
                continue
            except WebSocketDisconnect:
                print("Progress subscriber disconnected normally")
                break
            except Exception as e:
                print(f"Progress subscriber error: {str(e)}")
                break
    finally:
        if websocket in progress_subscribers:
            progress_subscribers.remove(websocket)
        await safe_close_websocket(websocket)
        print("Progress subscriber cleanup completed")

async def send_progress_update(subscriber: WebSocket, update: dict):
    """向单个订阅者发送进度更新"""
    try:
        if subscriber.client_state == WebSocketState.DISCONNECTED:
            if subscriber in progress_subscribers:
                progress_subscribers.remove(subscriber)
            return

        notification = {
            "jsonrpc": "2.0",
            "method": "analysis.progress",
            "params": update,
        }
        message = json.dumps(notification)
        await subscriber.send_text(message)
    except Exception as e:
        print(f"Error sending progress update: {str(e)}")
        if subscriber in progress_subscribers:
            progress_subscribers.remove(subscriber)
        await safe_close_websocket(subscriber)

async def broadcast_progress(update: dict):
    """向所有订阅者广播进度更新"""
    if not progress_subscribers:
        print("No progress subscribers available")  # 添加日志
        return
    
    # 为每个订阅者创建单独的任务
    tasks = []
    for subscriber in progress_subscribers.copy():  # 使用副本避免在迭代时修改
        task = asyncio.create_task(send_progress_update(subscriber, update))
        tasks.append(task)
    
    # 等待所有发送任务完成
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # 检查发送结果
        for result in results:
            if isinstance(result, Exception):
                print(f"Error in broadcast task: {str(result)}")

@fastapi_app.websocket("/ws/model")
async def ws_model(websocket: WebSocket):
    """处理模型调用的 WebSocket 端点"""
    await websocket.accept()
    print("Model connection open")

    try:
        # 1) 接收客户端的 JSON-RPC 请求
        req_text = await websocket.receive_text()
        request = json.loads(req_text)
        print("Received request:", request)

        # 2) 启动分析任务
        params = request["params"]
        
        # 默认使用所有分析师
        selected_analysts = [value for _, value in ANALYST_ORDER]
        
        # 默认使用 GPT-4
        model_name = "gpt-4o"
        model_provider = "OpenAI"
        
        try:
            queue = run_portfoliomind(
                cryptos=params["cryptos"],
                show_reasoning=params.get("show_reasoning", False),
                selected_analysts=selected_analysts,
                model_name=model_name,
                model_provider=model_provider
            )
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request["id"],
                "error": {
                    "code": -32000,
                    "message": f"Failed to start analysis: {str(e)}"
                }
            }
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await websocket.send_text(json.dumps(error_response))
            return

        # 3) 处理分析结果
        while True:
            try:
                update = await queue.get()

                # 立即广播进度更新
                await broadcast_progress(update)

                # 如果是最终结果，发送给模型调用客户端
                if update["type"] == "result":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request["id"],
                        "result": update["data"],
                    }
                    if websocket.client_state != WebSocketState.DISCONNECTED:
                        await websocket.send_text(json.dumps(response))
                    break
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "error": {
                        "code": -32000,
                        "message": f"Error during analysis: {str(e)}"
                    }
                }
                if websocket.client_state != WebSocketState.DISCONNECTED:
                    await websocket.send_text(json.dumps(error_response))
                break

    except WebSocketDisconnect:
        print("Model connection closed normally")
    except Exception as e:
        print("Error:", str(e))
        error_response = {
            "jsonrpc": "2.0",
            "id": request.get("id", None),
            "error": {
                "code": -32000,
                "message": str(e)
            }
        }
        if websocket.client_state != WebSocketState.DISCONNECTED:
            try:
                await websocket.send_text(json.dumps(error_response))
            except Exception:
                pass
    finally:
        await safe_close_websocket(websocket)
        print("Model connection cleanup completed")

# 导出 FastAPI 应用
app = fastapi_app
