from fastapi import FastAPI, WebSocket, Request, Response
from typing import Dict, List
import json
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from chat.chat import agent
from chat.models import Message

app = FastAPI()

# 添加 CORS 支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境中应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat_endpoint(request: Request):
    """
    HTTP 端点用于接收用户消息并返回 AI 回复和分析结果
    """
    try:
        # 获取请求体
        body = await request.json()
        
        # 提取用户消息
        user_message = body.get("message", "")
        if not user_message:
            return Response(
                content=json.dumps({"error": "Message is required"}),
                media_type="application/json",
                status_code=400
            )
        
        # 获取会话 ID (可选)
        session_id = body.get("session_id", "default")
        
        # 使用 agent 处理消息
        response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": user_message}]}
        )
        
        # 准备返回数据
        result = {
            "ai_message": "",
            "analysis_result": None
        }
        
        # 提取工具调用结果
        if response.get("tool_calls"):
            for tool_call in response["tool_calls"]:
                if tool_call["name"] == "analyze_prediction":
                    analysis_result = tool_call.get("result", {})
                    if isinstance(analysis_result, dict) and "error" in analysis_result:
                        result["error"] = analysis_result["error"]
                    else:
                        result["analysis_result"] = analysis_result
        
        # 提取 AI 消息
        if "messages" in response and response["messages"]:
            last_message = response["messages"][-1]
            if hasattr(last_message, "content"):
                result["ai_message"] = last_message.content
            else:
                result["ai_message"] = last_message.get("content", "")
        
        return Response(
            content=json.dumps(result),
            media_type="application/json"
        )
        
    except Exception as e:
        print(f"Error in /chat endpoint: {str(e)}")
        return Response(
            content=json.dumps({"error": str(e)}),
            media_type="application/json",
            status_code=500
        )

# 用于启动服务器的函数
def start():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)

if __name__ == "__main__":
    start() 