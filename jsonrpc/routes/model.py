from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from src.main import run_analyst
from src.utils.analysts import ANALYST_ORDER, ANALYST_CONFIG

router = APIRouter()

@router.post("/model")
async def http_model(request: Request):
    """Handle model invocation via HTTP POST.
    
    支持以下参数:
    - cryptos: 要分析的加密货币列表（与address互斥）
    - address: 用户地址（与cryptos互斥）
    - show_reasoning: 是否显示推理过程
    - selected_analysts: 要使用的分析师列表，可选，默认根据输入类型自动选择
    - model_name: 使用的模型名称，可选，默认使用 gpt-4o
    - model_provider: 模型提供商，可选，默认使用 OpenAI
    """
    try:
        body = await request.json()
        params = body.get("params", {})
        request_id = body.get("id", None)

        # 验证输入参数
        cryptos = params.get("cryptos")
        address = params.get("address")
        
        if cryptos is None and address is None:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": "Either cryptos or address must be provided"
                }
            }, status_code=400)
            
        if cryptos is not None and address is not None:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": "cryptos and address cannot be provided simultaneously"
                }
            }, status_code=400)

        # 获取要使用的分析师列表
        selected_analysts = params.get("selected_analysts")
        if not selected_analysts:
            # 根据输入类型自动选择分析师
            if cryptos is not None:
                selected_analysts = ["crypto_narrative"]  # 使用配置中的key
            else:  # address is not None
                selected_analysts = ["investment_recommendation"]  # 使用配置中的key
        elif isinstance(selected_analysts, str):
            # 如果只指定了一个分析师，转换为列表
            selected_analysts = [selected_analysts]

        # 获取模型配置
        model_name = params.get("model_name", "gpt-4o")
        model_provider = params.get("model_provider", "OpenAI")

        try:
            queue = run_analyst(
                cryptos=cryptos,
                address=address,
                show_reasoning=params.get("show_reasoning", False),
                selected_analysts=selected_analysts,
                model_name=model_name,
                model_provider=model_provider
            )
        except Exception as e:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": f"Failed to start analysis: {str(e)}"
                }
            }, status_code=500)

        # 只返回最终结果
        while True:
            update = await queue.get()
            if update["type"] == "result":
                # 准备结果数据
                result_data = update.get("data", {})
                
                # 提取分析结果
                analyst_signals = result_data.get("analyst_signals", {})
                
                # 获取原始结果
                if "investment_recommendation_agent" in analyst_signals:
                    # 如果是投资建议分析师，直接返回原始结果
                    result = analyst_signals["investment_recommendation_agent"]
                    # 将字典格式转换为列表格式
                    if isinstance(result, dict):
                        try:
                            result = [{"token": k, "usd": v.get("usd", 0.0)} for k, v in result.items()]
                        except Exception as e:
                            print(f"Error converting result format: {str(e)}")
                            # 如果转换失败，尝试直接使用原始结果
                            result = result
                else:
                    # 其他分析师的结果保持原样
                    result = analyst_signals
                
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                })
    except Exception as e:
        print(f"ERROR - HTTP handler exception: {str(e)}")
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32000,
                "message": str(e)
            }
        }, status_code=500) 