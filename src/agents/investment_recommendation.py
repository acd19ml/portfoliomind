from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import json
from src.utils.llm import call_llm
from src.graph.state import AgentState, show_agent_reasoning
from src.utils.progress import progress
from langchain_core.messages import HumanMessage
from src.ml.xgboost_pred import get_top3_predictions
from src.tools.preference import get_user_preference
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class InvestmentRecommendation(BaseModel):
    usd: float = Field(description="Recommended investment amount in USD")
    confidence: float = Field(description="Confidence in the recommendation, between 0.0 and 100.0")
    reasoning: str = Field(description="Reasoning for the recommendation")

class InvestmentManagerOutput(BaseModel):
    result: list[dict] = Field(description="List of investment recommendations, each containing token and usd amount")

def prepare_investment_data(address: str) -> tuple[dict, pd.DataFrame]:
    """
    准备投资决策所需的数据
    
    Args:
        address: 用户地址
        
    Returns:
        tuple: (user_preference, predictions_df)
    """
    # 获取用户偏好
    user_preference = get_user_preference(address)
    
    # 使用tokens_number作为市值排名阈值获取预测结果
    market_cap_rank = int(user_preference["tokens_number"])
    predictions_df = get_top3_predictions(market_cap_rank)
    
    return user_preference, predictions_df

def calculate_investment_constraints(
    predictions_df: pd.DataFrame,
    user_preference: dict
) -> tuple[dict, float, float, float]:
    """
    计算投资约束条件
    
    Args:
        predictions_df: 预测结果DataFrame，包含前3个预测结果
        user_preference: 用户偏好，包含：
            - durationDays: 投资期限（天）
            - returnRate: 目标收益率
            - min_investment: 最小投资金额（美元）
            - max_investment: 最大投资金额（美元）
            - tokensNumber: 市值前xx个代币  
        
    Returns:
        tuple: (signals_by_crypto, min_investment, max_investment)
    """
    signals_by_crypto = {}
    
    # 从用户偏好中获取投资金额范围
    min_investment = float(user_preference.get("min_investment", 0.0))
    max_investment = float(user_preference.get("max_investment", 0.0))
    
    # 确保我们只处理前3个预测结果
    top_3_predictions = predictions_df.head(3)
    
    for _, row in top_3_predictions.iterrows():
        crypto = row['symbol']
        confidence = row['confidence'] * 100  # 转换为百分比
        
        signals_by_crypto[crypto] = {
            "signal": "bullish" if row['predicted_label'] == 1 else "bearish",
            "confidence": confidence,
            "reasoning": f"ML model prediction with {confidence:.1f}% confidence"
        }
    
    return signals_by_crypto, min_investment, max_investment

def investment_recommendation_agent(state: AgentState):
    """基于用户偏好和预测结果生成投资建议"""
    try:
        # 获取用户地址
        address = state["data"].get("address")
        
        if not address:
            raise ValueError("User address not provided")

        # 准备投资数据
        user_preference, predictions_df = prepare_investment_data(address)
        
        if predictions_df.empty:
            logger.error("No predictions available")
            raise ValueError("No predictions available")

        # 打印预测结果以便调试
        logger.info(f"Predictions DataFrame:\n{predictions_df}")

        # 确保预测结果包含必要的列
        required_columns = ['symbol', 'predicted_label', 'confidence']
        if not all(col in predictions_df.columns for col in required_columns):
            logger.error(f"Missing required columns in predictions. Required: {required_columns}, Got: {predictions_df.columns.tolist()}")
            raise ValueError("Invalid prediction results format")

        # 计算投资约束
        signals_by_crypto, min_investment, max_investment = calculate_investment_constraints(
            predictions_df,
            user_preference
        )

        if not signals_by_crypto:
            logger.error("No valid signals generated from predictions")
            raise ValueError("No valid investment signals available")

        # 打印信号数据
        logger.info(f"Signals by crypto:\n{json.dumps(signals_by_crypto, indent=2)}")
        logger.info(f"Investment constraints: min={min_investment}, max={max_investment}")

        progress.update_status("investment_manager", None, "Generating investment recommendations")

        # 生成投资建议
        result = generate_investment_recommendation(
            signals_by_crypto=signals_by_crypto,
            min_investment=min_investment,
            max_investment=max_investment,
            user_preference=user_preference,
            model_name=state["metadata"]["model_name"],
            model_provider=state["metadata"]["model_provider"],
        )

        # 打印原始结果
        logger.info(f"Original result:\n{json.dumps(result.model_dump(), indent=2)}")

        # 创建投资建议消息
        message = HumanMessage(
            content=json.dumps(result.model_dump()),
            name="investment_manager",
        )

        # 存储信号到状态中
        if "analyst_signals" not in state["data"]:
            state["data"]["analyst_signals"] = {}
        state["data"]["analyst_signals"]["investment_recommendation_agent"] = result.result

        # 添加空决策以防止"No trading decisions available"消息
        if "decisions" not in state["data"]:
            state["data"]["decisions"] = {}

        progress.update_status("investment_manager", None, "Done")

        return {"messages": [message], "data": state["data"]}

    except Exception as e:
        logger.error(f"Error in investment recommendation agent: {str(e)}")
        raise

def generate_investment_recommendation(
    signals_by_crypto: dict[str, dict],
    min_investment: float,
    max_investment: float,
    user_preference: dict,
    model_name: str,
    model_provider: str,
) -> InvestmentManagerOutput:
    """基于预测结果和用户偏好生成投资建议"""
    
    # 创建提示模板
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a crypto investment advisor making recommendations based on ML predictions and user preferences.

                Investment Rules:
                - Investment duration: {duration_days} days
                - Target return rate: {return_rate}%
                - Investment amount range: {min_investment} to {max_investment} USD
                - Recommend from the top {tokens_number} by market capitalization
                - Only recommend investments for the top 3 cryptocurrencies with highest confidence
                - Total investment amount should be between min_investment and max_investment
                - Allocate investment amounts based on prediction confidence
                - Higher confidence predictions should receive larger allocations

                Inputs:
                - signals_by_crypto: Dictionary of top 3 crypto → prediction signals
                - min_investment: Minimum investment amount in USD
                - max_investment: Maximum investment amount in USD
                - user_preference: User's investment preferences

                For each crypto, provide:
                - usd: Recommended investment amount in USD
                """
            ),
            (
                "human",
                """Based on the ML predictions and user preferences, make investment recommendations for the top 3 cryptocurrencies.

                User Preferences:
                {user_preference}

                Prediction Signals (Top 3 Cryptocurrencies):
                {signals_by_crypto}

                Investment Amounts (USD):
                - Minimum: {min_investment}
                - Maximum: {max_investment}

                Output strictly in JSON with the following structure:
                {{
                    "result": [
                        {{
                            "token": "CRYPTO1",
                            "usd": float (USD)
                        }},
                        {{
                            "token": "CRYPTO2",
                            "usd": float (USD)
                        }},
                        {{
                            "token": "CRYPTO3",
                            "usd": float (USD)
                    }}
                    ]
                }}
                """
            ),
        ]
    )

    # 格式化提示
    prompt = template.invoke({
        "user_preference": json.dumps(user_preference, indent=2),
        "signals_by_crypto": json.dumps(signals_by_crypto, indent=2),
        "min_investment": min_investment,
        "max_investment": max_investment,
        "duration_days": user_preference.get("duration_days", 0),
        "return_rate": user_preference.get("return_rate", 0.0),
        "tokens_number": user_preference.get("tokens_number", 0.0)
    })

    # 调用LLM获取投资建议
    return call_llm(
        prompt=prompt,
        model_name=model_name,
        model_provider=model_provider,
        pydantic_model=InvestmentManagerOutput,
        agent_name="investment_manager",
        temperature=0.1
    )