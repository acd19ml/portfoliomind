"""Constants and utilities related to analysts configuration."""

from src.agents.crypto_narrative_sentiment import crypto_narrative_agent
from src.agents.investment_recommendation import investment_recommendation_agent

# Define analyst configuration - single source of truth
ANALYST_CONFIG = {
    "crypto_narrative": {
        "display_name": "Crypto Narrative Analyst",
        "agent_func": crypto_narrative_agent,
        "order": 0,
    },
    "investment_recommendation": {
        "display_name": "Investment Recommendation",
        "agent_func": investment_recommendation_agent,
        "order": 1,
    },
}

# Derive ANALYST_ORDER from ANALYST_CONFIG for backwards compatibility
ANALYST_ORDER = [(config["display_name"], key) for key, config in sorted(ANALYST_CONFIG.items(), key=lambda x: x[1]["order"])]


def get_analyst_nodes():
    """Get the mapping of analyst keys to their (node_name, agent_func) tuples."""
    return {key: (f"{key}_agent", config["agent_func"]) for key, config in ANALYST_CONFIG.items()}
