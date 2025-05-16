from src.graph.state import AgentState, show_agent_reasoning
from src.tools.crypto_api import get_coins
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import json
from typing_extensions import Literal
from src.utils.progress import progress
from src.utils.llm import call_llm


class CryptoNarrativeSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str


def crypto_narrative_agent(state: AgentState):
    """
    Analyzes cryptocurrencies using narrative and sentiment analysis:
    1. Social sentiment and dominance
    2. Market dominance and trends
    3. Technical indicators (Galaxy Score, Alt Rank)
    4. Community engagement and growth
    """
    data = state["data"]
    symbols = data["symbols"]  # List of crypto symbols to analyze

    analysis_data = {}
    narrative_analysis = {}

    # Get all coins data
    progress.update_status("crypto_narrative_agent", None, "Fetching cryptocurrency data")
    coins = get_coins()

    for symbol in symbols:
        # Find the coin data for this symbol
        coin_data = next((coin for coin in coins if coin.symbol == symbol), None)
        if not coin_data:
            progress.update_status("crypto_narrative_agent", symbol, "Symbol not found")
            continue

        progress.update_status("crypto_narrative_agent", symbol, "Analyzing social sentiment")
        sentiment_analysis = analyze_social_sentiment(coin_data)

        progress.update_status("crypto_narrative_agent", symbol, "Analyzing market dominance")
        market_analysis = analyze_market_dominance(coin_data)

        progress.update_status("crypto_narrative_agent", symbol, "Analyzing technical indicators")
        technical_analysis = analyze_technical_indicators(coin_data)

        # Aggregate scoring
        total_score = sentiment_analysis["score"] + market_analysis["score"] + technical_analysis["score"]
        max_possible_score = 15  # total possible from the three analysis functions

        # Map total_score to signal
        if total_score >= 0.7 * max_possible_score:
            signal = "bullish"
        elif total_score <= 0.3 * max_possible_score:
            signal = "bearish"
        else:
            signal = "neutral"

        analysis_data[symbol] = {
            "signal": signal,
            "score": total_score,
            "max_score": max_possible_score,
            "sentiment_analysis": sentiment_analysis,
            "market_analysis": market_analysis,
            "technical_analysis": technical_analysis
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

    # Wrap results in a single message for the chain
    message = HumanMessage(content=json.dumps(narrative_analysis), name="crypto_narrative_agent")

    # Optionally display reasoning
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(narrative_analysis, "Crypto Narrative Agent")

    # Store signals in the overall state
    state["data"]["analyst_signals"]["crypto_narrative_agent"] = narrative_analysis

    progress.update_status("crypto_narrative_agent", None, "Done")

    return {"messages": [message], "data": state["data"]}


def analyze_social_sentiment(coin_data) -> dict:
    """
    Analyzes social sentiment metrics:
    1. Overall sentiment score
    2. Social volume and dominance
    3. Community engagement
    """
    score = 0
    details = []

    # 1. Overall sentiment
    if coin_data.sentiment is not None:
        if coin_data.sentiment >= 70:
            score += 3
            details.append(f"Strong positive sentiment: {coin_data.sentiment}%")
        elif coin_data.sentiment >= 50:
            score += 2
            details.append(f"Moderate positive sentiment: {coin_data.sentiment}%")
        else:
            details.append(f"Negative sentiment: {coin_data.sentiment}%")

    # 2. Social volume and dominance
    if coin_data.social_volume_24h is not None and coin_data.social_dominance is not None:
        if coin_data.social_dominance >= 10:
            score += 2
            details.append(f"High social dominance: {coin_data.social_dominance}%")
        elif coin_data.social_dominance >= 5:
            score += 1
            details.append(f"Moderate social dominance: {coin_data.social_dominance}%")
        else:
            details.append(f"Low social dominance: {coin_data.social_dominance}%")

    # 3. Community engagement
    if coin_data.interactions_24h is not None:
        if coin_data.interactions_24h >= 1000000:
            score += 2
            details.append(f"High community engagement: {coin_data.interactions_24h:,} interactions")
        elif coin_data.interactions_24h >= 100000:
            score += 1
            details.append(f"Moderate community engagement: {coin_data.interactions_24h:,} interactions")
        else:
            details.append(f"Low community engagement: {coin_data.interactions_24h:,} interactions")

    return {"score": score, "details": "; ".join(details)}


def analyze_market_dominance(coin_data) -> dict:
    """
    Analyzes market dominance and trends:
    1. Market dominance
    2. Market cap rank
    3. Price trends
    """
    score = 0
    details = []

    # 1. Market dominance
    if coin_data.market_dominance is not None:
        if coin_data.market_dominance >= 50:
            score += 3
            details.append(f"Strong market dominance: {coin_data.market_dominance}%")
        elif coin_data.market_dominance >= 20:
            score += 2
            details.append(f"Significant market dominance: {coin_data.market_dominance}%")
        elif coin_data.market_dominance >= 5:
            score += 1
            details.append(f"Moderate market dominance: {coin_data.market_dominance}%")
        else:
            details.append(f"Low market dominance: {coin_data.market_dominance}%")

    # 2. Market cap rank
    if coin_data.market_cap_rank is not None:
        if coin_data.market_cap_rank <= 10:
            score += 2
            details.append(f"Top 10 market cap rank: #{coin_data.market_cap_rank}")
        elif coin_data.market_cap_rank <= 50:
            score += 1
            details.append(f"Top 50 market cap rank: #{coin_data.market_cap_rank}")
        else:
            details.append(f"Lower market cap rank: #{coin_data.market_cap_rank}")

    # 3. Price trends
    if coin_data.percent_change_24h is not None:
        if coin_data.percent_change_24h > 5:
            score += 1
            details.append(f"Strong 24h price increase: {coin_data.percent_change_24h}%")
        elif coin_data.percent_change_24h < -5:
            details.append(f"Significant 24h price decrease: {coin_data.percent_change_24h}%")
        else:
            details.append(f"Stable 24h price movement: {coin_data.percent_change_24h}%")

    return {"score": score, "details": "; ".join(details)}


def analyze_technical_indicators(coin_data) -> dict:
    """
    Analyzes technical indicators:
    1. Galaxy Score
    2. Alt Rank
    3. Volatility
    """
    score = 0
    details = []

    # 1. Galaxy Score
    if coin_data.galaxy_score is not None:
        if coin_data.galaxy_score >= 70:
            score += 3
            details.append(f"Strong Galaxy Score: {coin_data.galaxy_score}")
        elif coin_data.galaxy_score >= 50:
            score += 2
            details.append(f"Moderate Galaxy Score: {coin_data.galaxy_score}")
        else:
            details.append(f"Low Galaxy Score: {coin_data.galaxy_score}")

    # 2. Alt Rank
    if coin_data.alt_rank is not None:
        if coin_data.alt_rank <= 50:
            score += 2
            details.append(f"Strong Alt Rank: #{coin_data.alt_rank}")
        elif coin_data.alt_rank <= 200:
            score += 1
            details.append(f"Moderate Alt Rank: #{coin_data.alt_rank}")
        else:
            details.append(f"Lower Alt Rank: #{coin_data.alt_rank}")

    # 3. Volatility
    if coin_data.volatility is not None:
        if coin_data.volatility < 0.01:
            score += 1
            details.append(f"Low volatility: {coin_data.volatility:.4f}")
        elif coin_data.volatility > 0.05:
            details.append(f"High volatility: {coin_data.volatility:.4f}")
        else:
            details.append(f"Moderate volatility: {coin_data.volatility:.4f}")

    return {"score": score, "details": "; ".join(details)}


def generate_narrative_output(
    symbol: str,
    analysis_data: dict[str, any],
    model_name: str,
    model_provider: str,
) -> CryptoNarrativeSignal:
    """
    Generates a crypto investment decision based on narrative and sentiment analysis:
    - Social sentiment and community engagement
    - Market dominance and trends
    - Technical indicators and rankings
    - Return the result in a JSON structure: { signal, confidence, reasoning }
    """

    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a Crypto Narrative Analysis AI agent, making investment decisions using these principles:
            1. Analyze social sentiment and community engagement to gauge market psychology
            2. Consider market dominance and trends to understand market position
            3. Evaluate technical indicators (Galaxy Score, Alt Rank) for market health
            4. Look for strong community growth and engagement
            5. Consider both short-term momentum and long-term narrative strength
            
            When providing your reasoning, be thorough and specific by:
            1. Explaining the key sentiment metrics that influenced your decision
            2. Highlighting the market dominance and position indicators
            3. Referencing technical indicators and their implications
            4. Providing quantitative evidence with precise numbers
            5. Comparing current metrics to historical patterns
            6. Using a balanced, analytical voice in your explanation
            
            For example, if bullish: "The cryptocurrency shows strong social sentiment (75%) and high community engagement (1.5M interactions). Market dominance of 15% indicates significant market presence, while a Galaxy Score of 80 suggests strong technical fundamentals..."
            For example, if bearish: "Despite high social volume, the sentiment score of 35% indicates negative market psychology. The Alt Rank of 500 suggests underperformance relative to peers, while high volatility of 0.08 indicates market instability..."
                        
            Return a rational recommendation: bullish, bearish, or neutral, with a confidence level (0-100) and thorough reasoning.
            """,
            ),
            (
                "human",
                """Based on the following analysis, create a crypto narrative investment signal:

            Analysis Data for {symbol}:
            {analysis_data}

            Return JSON exactly in this format:
            {{
              "signal": "bullish" or "bearish" or "neutral",
              "confidence": float (0-100),
              "reasoning": "string"
            }}
            """,
            ),
        ]
    )

    prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "symbol": symbol})

    def create_default_narrative_signal():
        return CryptoNarrativeSignal(signal="neutral", confidence=0.0, reasoning="Error in generating analysis; defaulting to neutral.")

    return call_llm(
        prompt=prompt,
        model_name=model_name,
        model_provider=model_provider,
        pydantic_model=CryptoNarrativeSignal,
        agent_name="crypto_narrative_agent",
        default_factory=create_default_narrative_signal,
    )
