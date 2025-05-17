import asyncio
import json
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

def print_analysis_result(result):
    """打印分析结果"""
    if isinstance(result, list) and len(result) > 0:
        # 处理 TextContent 对象
        content = result[0]
        if hasattr(content, 'text'):
            try:
                data = json.loads(content.text)
                if data.get("success"):
                    print("\nAnalysis Results:")
                    print(json.dumps(data.get("data", {}), indent=2))
                else:
                    print(f"Analysis failed: {data.get('error', 'Unknown error')}")
            except json.JSONDecodeError as e:
                print(f"Error decoding result: {e}")
                print(f"Raw result: {content.text}")
        else:
            print(f"Unexpected result format: {result}")
    else:
        print(f"Unexpected result: {result}")

async def test_mcp_client():
    # 创建 FastMCP 客户端
    client = Client(StreamableHttpTransport("http://127.0.0.1:9000/mcp"))
    
    try:
        async with client:
            # 测试 analyze_portfolio
            result = await client.call_tool(
                "analyze_portfolio",
                {
                    "symbols": ["BTC", "ETH"],
                    "show_reasoning": True
                }
            )
            print_analysis_result(result)

            # 测试 analyze_portfolio_stream
            try:
                # 获取状态更新列表
                updates = await client.call_tool(
                    "analyze_portfolio_stream",
                    {
                        "symbols": ["BTC", "ETH"],
                        "show_reasoning": True
                    }
                )
                
                # 处理状态更新列表
                for update in updates:
                    try:
                        if isinstance(update, str):
                            update = json.loads(update)
                        elif hasattr(update, 'text'):
                            try:
                                update = json.loads(update.text)
                            except json.JSONDecodeError:
                                print(f"Raw update text: {update.text}")
                                continue
                                
                        # 打印状态更新
                        if isinstance(update, dict):
                            if update.get("type") == "status":
                                print(f"Status Update: {update.get('agent')} - {update.get('crypto', 'Overall')}: {update.get('status')}")
                            elif update.get("type") == "result":
                                print("\nFinal Result:")
                                print(json.dumps(update.get("data", {}), indent=2))
                                break
                    except json.JSONDecodeError as e:
                        print(f"Error decoding update: {e}")
                        print(f"Raw update: {update}")
                    except Exception as e:
                        print(f"Error processing update: {e}")
                        print(f"Raw update: {update}")
                        
            except Exception as e:
                print(f"Error in stream processing: {e}")
                
    except Exception as e:
        print(f"Error in client connection: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(test_mcp_client())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}") 