from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import json
import asyncio
from typing import Set
from starlette.websockets import WebSocketState

router = APIRouter()

# 存储活跃的进度订阅者
progress_subscribers: Set[WebSocket] = set()

async def safe_close_websocket(websocket: WebSocket):
    """安全地关闭 WebSocket 连接"""
    if websocket.client_state != WebSocketState.DISCONNECTED:
        try:
            await websocket.close()
        except Exception:
            pass

@router.websocket("/ws/progress")
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
        print("No progress subscribers available")
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