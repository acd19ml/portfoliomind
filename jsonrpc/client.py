import asyncio
import json
import websockets

async def test_portfolio_analysis():
    uri = "ws://localhost:8000/ws/portfolio"
    async with websockets.connect(uri) as websocket:
        # 发送分析请求
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "analyzePortfolio",
            "params": {
                "cryptos": ["BTC", "ETH"],
                "show_reasoning": True
            }
        }
        await websocket.send(json.dumps(request))
        print("Request sent:", request)

        # 接收响应
        while True:
            try:
                response = await websocket.recv()
                data = json.loads(response)
                
                if "method" in data:  # 进度通知
                    print(f"\nProgress: {data['params']}")
                elif "error" in data:  # 错误响应
                    print(f"\nError: {data['error']['message']}")
                    break
                elif "result" in data:  # 成功响应
                    print(f"\nFinal result: {data['result']}")
                    break
                    
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break

if __name__ == "__main__":
    asyncio.run(test_portfolio_analysis()) 