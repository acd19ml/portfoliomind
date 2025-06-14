from src.graph.state import AgentState, show_agent_reasoning
from src.tools.api import get_coins
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import json
from typing_extensions import Literal
from src.utils.progress import progress
from src.utils.llm import call_llm
from src.ml.xgboost_pred import predict_from_coin_data


class CryptoNarrativeSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: Literal["high confidence in price increase", "moderate confidence in price increase", "low confidence in price increase", "no confidence in price increase"]
    reasoning: str


def get_confidence_level(confidence: float) -> str:
    """
    将数值置信度转换为描述性置信度
    """
    if confidence > 0.7:
        return "high confidence in price increase"
    elif confidence > 0.45:
        return "moderate confidence in price increase"
    elif confidence > 0.35:
        return "low confidence in price increase"
    else:
        return "no confidence in price increase"


def crypto_narrative_agent(state: AgentState):
    """
    Analyzes cryptocurrencies using ML model predictions and narrative analysis:
    1. Uses XGBoost model for technical and market analysis
    2. Combines model predictions with narrative analysis
    3. Provides comprehensive investment signals
    """
    data = state["data"]
    symbols = data["symbols"]  # List of crypto symbols to analyze
    # print(f"\nAnalyzing symbols: {symbols}")

    analysis_data = {}
    narrative_analysis = {}

    # Get only the specified coins data
    progress.update_status("crypto_narrative_agent", None, "Fetching cryptocurrency data")
    coins = get_coins(symbols)  # 只获取指定的币种数据
    # print(f"Fetched {len(coins)} coins for analysis")

    # Get model predictions for the specified coins
    progress.update_status("crypto_narrative_agent", None, "Running ML model predictions")
    predictions_df = predict_from_coin_data(coins)
    # print(f"\nPredictions DataFrame shape: {predictions_df.shape}")
    # print("Predictions DataFrame head:")
    # print(predictions_df.head())

    for symbol in symbols:
        # print(f"\nProcessing symbol: {symbol}")
        # Find the coin data for this symbol
        coin_data = next((coin for coin in coins if coin.symbol == symbol), None)
        if not coin_data:
            # print(f"Symbol {symbol} not found in coins data")
            progress.update_status("crypto_narrative_agent", symbol, "Symbol not found")
            continue

        # Get prediction for this symbol
        symbol_prediction = predictions_df[predictions_df['symbol'] == symbol].iloc[0] if len(predictions_df[predictions_df['symbol'] == symbol]) > 0 else None
        
        if symbol_prediction is None:
            # print(f"No prediction available for symbol {symbol}")
            progress.update_status("crypto_narrative_agent", symbol, "No prediction available")
            continue

        # print(f"Found prediction for {symbol}:")
        # print(symbol_prediction)

        # Map prediction to signal
        if symbol_prediction['predicted_label'] == 1:
            signal = "bullish"
        else:
            signal = "bearish"

        analysis_data[symbol] = {
            "signal": signal,
            "confidence": get_confidence_level(float(symbol_prediction['confidence'])),
            "model_prediction": {
                "predicted_label": int(symbol_prediction['predicted_label']),
                "confidence": float(symbol_prediction['confidence'])
            }
        }

        progress.update_status("crypto_narrative_agent", symbol, "Generating narrative analysis")
        narrative_output = generate_narrative_output(
            symbol=symbol,
            analysis_data=analysis_data,
            model_name=state["metadata"]["model_name"],
            model_provider=state["metadata"]["model_provider"],
        )

        narrative_analysis[symbol] = {
            "signal": narrative_output.signal,
            "confidence": narrative_output.confidence,
            "reasoning": narrative_output.reasoning
        }

        progress.update_status("crypto_narrative_agent", symbol, "Done")

    # print("\nFinal narrative analysis:")
    # print(json.dumps(narrative_analysis, indent=2))

    # Wrap results in a single message for the chain
    message = HumanMessage(content=json.dumps(narrative_analysis), name="crypto_narrative_agent")

    # Optionally display reasoning
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(narrative_analysis, "Crypto Narrative Agent")

    # Store signals in the overall state
    if "analyst_signals" not in state["data"]:
        state["data"]["analyst_signals"] = {}
    state["data"]["analyst_signals"]["crypto_narrative_agent"] = narrative_analysis

    # Add empty decisions to prevent "No trading decisions available" message
    if "decisions" not in state["data"]:
        state["data"]["decisions"] = {}

    progress.update_status("crypto_narrative_agent", None, "Done")

    return {"messages": [message], "data": state["data"]}


def generate_narrative_output(
    symbol: str,
    analysis_data: dict[str, any],
    model_name: str,
    model_provider: str,
) -> CryptoNarrativeSignal:
    """
    Generates a crypto investment decision based on ML model predictions and narrative analysis:
    - Uses model predictions for technical and market analysis
    - Provides comprehensive reasoning based on model outputs
    - Return the result in a JSON structure: { signal, confidence, reasoning }
    """
    # Get current market data for the symbol
    coins = get_coins()
    coin_data = next((coin for coin in coins if coin.symbol == symbol), None)
    
    if coin_data:
        # Convert all numeric values to float to ensure JSON serialization
        current_market_data = {
            "Technical Indicators": {
                "Galaxy Score": float(coin_data.galaxy_score) if coin_data.galaxy_score is not None else None,
                "Alt Rank": int(coin_data.alt_rank) if coin_data.alt_rank is not None else None,
                "Volatility": float(coin_data.volatility) if coin_data.volatility is not None else None
            },
            "Market Metrics": {
                "Market Cap Rank": int(coin_data.market_cap_rank) if coin_data.market_cap_rank is not None else None,
                "Market Dominance": float(coin_data.market_dominance) if coin_data.market_dominance is not None else None,
                "24h Volume": float(coin_data.volume_24h) if hasattr(coin_data, 'volume_24h') and coin_data.volume_24h is not None else None
            },
            "Social Metrics": {
                "Sentiment": float(coin_data.sentiment) if coin_data.sentiment is not None else None,
                "Social Volume (24h)": int(coin_data.social_volume_24h) if coin_data.social_volume_24h is not None else None,
                "Social Dominance": float(coin_data.social_dominance) if coin_data.social_dominance is not None else None,
                "Interactions (24h)": int(coin_data.interactions_24h) if coin_data.interactions_24h is not None else None
            },
            "Price Changes": {
                "1h Change": float(coin_data.percent_change_1h) if hasattr(coin_data, 'percent_change_1h') and coin_data.percent_change_1h is not None else None,
                "7d Change": float(coin_data.percent_change_7d) if hasattr(coin_data, 'percent_change_7d') and coin_data.percent_change_7d is not None else None,
                "30d Change": float(coin_data.percent_change_30d) if hasattr(coin_data, 'percent_change_30d') and coin_data.percent_change_30d is not None else None
            }
        }
    else:
        current_market_data = "Market data not available"

    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a Crypto Analysis AI agent. Your role is to interpret machine learning model outputs and current market data to generate investment signals in the cryptocurrency market. Follow these principles:

                    1. Consider both the model's prediction (`predicted_label`) and its **confidence in price increase** (`confidence`, between 0 and 1).
                    2. If `predicted_label` is 1, the model predicts a potential price increase. Otherwise, the model predicts no price increase.
                    3. Express **confidence in price increase** using semantic descriptors only (not numeric values):
                        - confidence > 0.7 → "high confidence in price increase"
                        - 0.45 < confidence ≤ 0.7 → "moderate confidence in price increase"
                        - 0.35 < confidence ≤ 0.45 → "low confidence in price increase"
                        - confidence ≤ 0.35 → model predicts no price increase, return "no confidence in price increase"

                    4. The model is conservative when predicting price increases. Even moderate or low confidence signals should be interpreted with caution.
                    5. Use a balanced, analytical, and professional tone. Avoid exaggeration or overconfidence.

                When composing your response:
                - Clearly state the model's directional prediction (bullish, bearish, or neutral)
                - Describe **confidence in price increase** using one of the approved phrases
                - Explain the rationale behind the prediction using the data provided in `current_market_data` and `analysis_data`
                - Highlight any uncertainty or signal weakness when applicable

                ### Output strictly in the following JSON format:
                {{
                    "signal": "bullish" or "bearish" or "neutral",
                    "confidence": "high confidence in price increase" or "moderate confidence in price increase" or "low confidence in price increase" or "no confidence in price increase",
                    "reasoning": "string"
                }}
                """
            ),
            (
                "human",
                """Based on the following analysis and current market data, create a crypto investment signal:

            Current Market Data for {symbol}:
            {current_market_data}

            Model Analysis Data:
            {analysis_data}
            """
            )
        ]
    )

    prompt = template.invoke({
        "analysis_data": json.dumps(analysis_data, indent=2),
        "symbol": symbol,
        "current_market_data": json.dumps(current_market_data, indent=2)
    })

    def create_default_narrative_signal():
        return CryptoNarrativeSignal(signal="neutral", confidence="no confidence in price increase", reasoning="Error in generating analysis; defaulting to neutral.")

    return call_llm(
        prompt=prompt,
        model_name=model_name,
        model_provider=model_provider,
        pydantic_model=CryptoNarrativeSignal,
        agent_name="crypto_narrative_agent",
        default_factory=create_default_narrative_signal,
        temperature=0.1
    )
