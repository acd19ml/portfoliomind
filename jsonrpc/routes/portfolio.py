from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from jsonrpc.services.portfolio import create_portfolio

router = APIRouter()

@router.post("/portfolio")
async def http_portfolio(request: Request):
    """Handle portfolio creation via HTTP POST."""
    try:
        body = await request.json()
        params = body.get("params", {})
        request_id = body.get("id", None)

        # 获取地址
        address = params.get("address")
        
        if not address:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": "Missing required parameter: address"
                }
            }, status_code=400)

        try:
            # 创建投资组合
            portfolio = create_portfolio(address)
            
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": portfolio
            })
            
        except Exception as e:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": f"Failed to create portfolio: {str(e)}"
                }
            }, status_code=500)

    except Exception as e:
        print(f"ERROR - Portfolio handler exception: {str(e)}")
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32000,
                "message": str(e)
            }
        }, status_code=500) 