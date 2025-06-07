from fastapi import FastAPI, WebSocket, Request, Response
from fastapi.responses import StreamingResponse
from typing import Dict, List, AsyncGenerator
import json
import asyncio
import logging
from fastapi.middleware.cors import CORSMiddleware
from chat.chat import agent
from chat.models import Message
from contextlib import asynccontextmanager, AsyncExitStack
from contextlib import suppress

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="Chat API",
    description="Chat API with streaming support",
    version="1.0.0"
)

# 添加 CORS 支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def stream_chat_response(message: str) -> AsyncGenerator[str, None]:
    """流式生成 AI 响应"""
    async with AsyncExitStack() as stack:
        try:
            logger.debug(f"Starting agent stream for message: {message}")
            
            # 使用 astream_events V1 来获取结构化的事件流
            async for event in agent.astream_events(
                {"messages": [{"role": "user", "content": message}]},
                version="v1"
            ):
                kind = event["event"]
                
                # 当工具开始执行时，立即向客户端发送一个状态更新
                if kind == "on_tool_start":
                    tool_name = event["name"]
                    yield f"data: {json.dumps({'type': 'status', 'content': f'正在调用工具: {tool_name}...'})}\n\n"

                # 当聊天模型正在流式输出 token 时
                elif kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        # 将 token 作为 SSE 事件发送
                        yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
                        await asyncio.sleep(0.01)  # 轻微延迟以平滑输出
                
                # 当工具调用结束时
                elif kind == "on_tool_end":
                    # 检查是否是我们的分析工具
                    if event["name"] == "analyze_prediction":
                        analysis_result = event["data"].get("output", {})
                        if isinstance(analysis_result, dict) and "error" not in analysis_result:
                            # 将分析结果作为 SSE 事件发送
                            yield f"data: {json.dumps({'type': 'analysis', 'content': analysis_result})}\n\n"

            # 所有事件处理完毕，发送结束标记
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Error in stream_chat_response: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
        finally:
            # 确保资源被正确清理
            with suppress(Exception):
                await asyncio.sleep(0.1)

# 确保路由正确注册
@app.post("/chat/stream")
async def chat_stream_endpoint(request: Request):
    """
    流式聊天端点，支持实时输出 AI 响应
    """
    logger.debug(f"Received request to /chat/stream")
    try:
        # 获取请求体
        body = await request.json()
        logger.debug(f"Request body: {body}")
        
        # 提取用户消息
        user_message = body.get("message", "")
        session_id = body.get("session_id", "default")
        
        if not user_message:
            return Response(
                content=json.dumps({"error": "Message is required"}),
                media_type="application/json",
                status_code=400
            )
        
        # 返回流式响应
        return StreamingResponse(
            stream_chat_response(user_message),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )
        
    except Exception as e:
        logger.error(f"Error in /chat/stream endpoint: {str(e)}")
        return Response(
            content=json.dumps({"error": str(e)}),
            media_type="application/json",
            status_code=500
        )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    logger.info("Starting server...")
    logger.info("Registered routes:")
    for route in app.routes:
        logger.info(f"Route: {route.path}, methods: {route.methods}")
    yield
    # 关闭时
    logger.info("Shutting down server...")

# 设置应用的生命周期管理器
app.router.lifespan_context = lifespan

def start():
    import uvicorn
    logger.info("Starting server on 0.0.0.0:8008")
    uvicorn.run(
        app, 
        host="0.0.0.0",
        port=8008,
        log_level="debug",
        reload=False,
        workers=1,
        timeout_keep_alive=30
    )

if __name__ == "__main__":
    start()