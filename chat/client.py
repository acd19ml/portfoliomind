import requests
import json
import argparse
import sseclient
import os

def get_server_url(port=8008):
    """根据环境获取服务器 URL"""
    if 'DOCKER_ENV' in os.environ:
        return f"http://host.docker.internal:{port}"
    return f"http://localhost:{port}"

def chat_with_ai(message, server_url=get_server_url(8008)):
    """
    向 AI 发送消息并获取回复
    
    Args:
        message (str): 用户消息
        server_url (str): 服务器 URL
    
    Returns:
        dict: 包含 AI 回复和分析结果的字典
    """
    url = f"{server_url}/chat"
    
    try:
        # 发送 POST 请求
        response = requests.post(
            url,
            json={"message": message},
            headers={"Content-Type": "application/json"}
        )
        
        # 检查响应状态
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            print(f"Error: Server returned status code {response.status_code}")
            print(response.text)
            return None
    
    except Exception as e:
        print(f"Error communicating with server: {str(e)}")
        return None
    
def chat_with_ai_stream(message, server_url=get_server_url(8008)):
    """
    使用流式接口与 AI 聊天
    
    Args:
        message (str): 用户消息
        server_url (str): 服务器 URL
    
    Returns:
        None: 直接打印流式响应
    """
    url = f"{server_url}/chat/stream"
    print(f"Sending request to: {url}")
    
    try:
        # 发送 POST 请求
        response = requests.post(
            url,
            json={"message": message},
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            },
            stream=True,
            timeout=60  # 增加超时时间
        )
        
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.status_code == 200:
            print("\n" + "=" * 50)
            print("AI Response:")
            print("=" * 50)
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    # SSE 消息以 "data: " 开头
                    if decoded_line.startswith('data: '):
                        data_str = decoded_line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            if data.get("type") == "token":
                                print(data.get("content", ""), end="", flush=True)
                            elif data.get("type") == "analysis":
                                print("\n\n" + "=" * 50)
                                print("Analysis Result:")
                                print("=" * 50)
                                print(json.dumps(data.get("content", {}), indent=2))
                            elif data.get("type") == "status":
                                print(f"\n[{data.get('content', '...')}]", end="", flush=True)
                            elif data.get("type") == "error":
                                print(f"\nServer Error: {data.get('content', 'Unknown error')}")
                        except json.JSONDecodeError:
                            print(f"\n[RAW DATA] Could not decode JSON: {data_str}")
            print("\n")
        else:
            print(f"Error: Server returned status code {response.status_code}")
            print(f"Response text: {response.text}")
    
    except requests.exceptions.RequestException as e:
        print(f"Network error: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

def display_result(result):
    """
    格式化显示结果
    
    Args:
        result (dict): 包含 AI 回复和分析结果的字典
    """
    if not result:
        return
    
    print("\n" + "=" * 50)
    print("AI Response:")
    print("=" * 50)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    # 显示 AI 消息
    print(result.get("ai_message", "No message"))
    
    # 显示分析结果
    if result.get("analysis_result"):
        print("\n" + "=" * 50)
        print("Analysis Result:")
        print("=" * 50)
        print(json.dumps(result["analysis_result"], indent=2))

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Chat with AI Assistant")
    parser.add_argument("--message", "-m", type=str, help="Message to send to the AI")
    parser.add_argument("--server", "-s", type=str, default=get_server_url(8008), 
                        help=f"Server URL (default: {get_server_url(8008)})")
    parser.add_argument("--stream", action="store_true",
                        help="Use streaming mode for responses")
    args = parser.parse_args()
    
    if args.message:
        # 使用命令行参数
        if args.stream:
            chat_with_ai_stream(args.message, args.server)
        else:
            result = chat_with_ai(args.message, args.server)
            display_result(result)
    else:
        # 交互模式
        print("Chat with AI Assistant (type 'exit' to quit)")
        print("=" * 50)
        
        while True:
            message = input("\nYou: ")
            if message.lower() in ["exit", "quit", "bye"]:
                break
            
            if args.stream:
                chat_with_ai_stream(message, args.server)
            else:
                result = chat_with_ai(message, args.server)
                display_result(result)

if __name__ == "__main__":
    main() 