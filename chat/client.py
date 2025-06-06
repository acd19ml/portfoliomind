import requests
import json
import argparse

def chat_with_ai(message, server_url="http://localhost:8008"):
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
    parser.add_argument("--server", "-s", type=str, default="http://localhost:8008", 
                        help="Server URL (default: http://localhost:8008)")
    args = parser.parse_args()
    
    if args.message:
        # 使用命令行参数
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
            
            result = chat_with_ai(message, args.server)
            display_result(result)

if __name__ == "__main__":
    main() 