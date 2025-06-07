from langchain_core.tools import tool
import httpx

@tool
async def analyze_prediction(cryptos: list[str], show_reasoning: bool = False) -> dict:
    """
    Analyze crypto predictions by calling the /model HTTP endpoint.
    This tool analyzes specific cryptocurrencies and provides trading recommendations.
    
    Args:
        cryptos: List of crypto symbols to analyze (e.g., ["BTC", "ETH"])
        show_reasoning: Whether to show reasoning from each agent
        
    Returns:
        The analysis result as a dictionary containing trading recommendations
    """
    url = "http://localhost:8000/model"
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "analyze_portfolio",
        "params": {
            "cryptos": cryptos,
            "show_reasoning": show_reasoning
        }
    }
    try:
        # print(f"Sending request to {url} with data: {request}")
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=request, timeout=60)  # 增加超时时间
            # print(f"Response status: {response.status_code}")
            
            # 如果状态码不是200，则抛出异常
            response.raise_for_status()
            
            # 解析响应数据
            data = response.json()
            # print(f"Response data: {data}")
            
            if "result" in data:
                result = data["result"]
                
                # 返回原始结果，即使可能为空
                return result or {"error": "Empty analysis result"}
            elif "error" in data:
                error_msg = data.get("error", {}).get("message", "Unknown error")
                print(f"Server returned error: {error_msg}")
                return {"error": error_msg}
            else:
                print(f"Unexpected response format: {data}")
                return {"error": "Unknown response format", "raw_response": data}
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error: {e.response.status_code} - {e.response.text}"
        print(error_msg)
        return {"error": error_msg}
    except httpx.RequestError as e:
        error_msg = f"Request error: {str(e)} - {repr(e)}"
        print(error_msg)
        # 添加网络诊断信息
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("localhost", 8000))
            conn_status = "Connection test successful"
            s.close()
        except Exception as conn_e:
            conn_status = f"Connection test failed: {str(conn_e)}"
        print(f"Connection diagnostic: {conn_status}")
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

@tool
async def analyze_portfolio(address: str, show_reasoning: bool = False) -> dict:
    """
    Analyze a crypto portfolio by calling the /model HTTP endpoint.
    This tool analyzes a user's portfolio based on their wallet address and provides investment recommendations.
    
    Args:
        address: User's wallet address to analyze
        show_reasoning: Whether to show reasoning from each agent
        
    Returns:
        The analysis result as a dictionary containing investment recommendations
    """
    url = "http://localhost:8000/model"
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "analyze_portfolio",
        "params": {
            "address": address,
            "show_reasoning": show_reasoning
        }
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=request, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            if "result" in data:
                result = data["result"]
                
                
                return result or {"error": "Empty analysis result"}
            elif "error" in data:
                error_msg = data.get("error", {}).get("message", "Unknown error")
                print(f"Server returned error: {error_msg}")
                return {"error": error_msg}
            else:
                print(f"Unexpected response format: {data}")
                return {"error": "Unknown response format", "raw_response": data}
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP error: {e.response.status_code} - {e.response.text}"
        print(error_msg)
        return {"error": error_msg}
    except httpx.RequestError as e:
        error_msg = f"Request error: {str(e)} - {repr(e)}"
        print(error_msg)
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("localhost", 8000))
            conn_status = "Connection test successful"
            s.close()
        except Exception as conn_e:
            conn_status = f"Connection test failed: {str(conn_e)}"
        print(f"Connection diagnostic: {conn_status}")
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        return {"error": error_msg} 
