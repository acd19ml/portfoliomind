import asyncio
from chat.chat import agent
from chat.utils import pretty_print
import json

async def main():
    try:
        # 使用 ainvoke 异步调用 agent
        response = await agent.ainvoke(
            {"messages": [{
                "role": "user", 
                "content": "I want a detailed analysis of BTC and ETH with reasoning"
            }]}
        )
        
        # 检查 response 中是否包含 tool_calls
        if response.get("tool_calls"):
            for tool_call in response["tool_calls"]:
                if tool_call["name"] == "analyze_prediction":
                    result = tool_call.get("result", {})
                    
                    # 检查结果是否有错误
                    if isinstance(result, dict) and "error" in result:
                        print(f"Error: {result['error']}")
                    elif result and isinstance(result, dict) and ("BTC" in result or "ETH" in result):
                        print(json.dumps(result, indent=2))
        
        # 输出 AI 消息
        if "messages" in response and response["messages"]:
            last_message = response["messages"][-1]
            if hasattr(last_message, "pretty_print"):
                last_message.pretty_print()
            else:
                print(last_message.get("content", ""))
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())