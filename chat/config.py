import os
from dotenv import load_dotenv

_ = load_dotenv()

# User profile configuration
profile = {
    "_id": "0x4547808f6586491c44b41a7833893912383d78c9",
    "tokens": [
        {
            "symbol": "BTC",
            "balance": 1.23,
            "network": "other networks",
            "in_wallet": False
        },
        {
            "symbol": "ETH",
            "balance": 0,
            "network": "ethereum",
            "in_wallet": True
        },
        {
            "symbol": "WETH",
            "balance": 0,
            "network": "ethereum",
            "in_wallet": True
        }
    ],
    "risk_level": "high"
}

# Email triage rules
prompt_instructions = {
    "triage_rules": {
        "high_risk": "Recommend from the top 5000 cryptocurrencies by market capitalization",
        "medium_risk": "Recommend from the top 1000 cryptocurrencies by market capitalization",
        "low_risk": "Recommend from the top 100 cryptocurrencies by market capitalization",
    },
    "agent_instructions": "Use these tools when appropriate to help manage John's tasks efficiently."
}

# Example email for testing
example_email = {
    "author": "Alice Smith <alice.smith@company.com>",
    "to": "John Doe <john.doe@company.com>",
    "subject": "Quick question about API documentation",
    "email_thread": """
Hi John,

I was reviewing the API documentation for the new authentication service and noticed a few endpoints seem to be missing from the specs. Could you help clarify if this was intentional or if we should update the docs?

Specifically, I'm looking at:
- /auth/refresh
- /auth/validate

Thanks!
Alice""",
} 