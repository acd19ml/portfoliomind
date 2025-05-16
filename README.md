# Portfoliomind

AI-Agents that uses multiple LLM agents to analyze and trade crypto.

## Features

- Multiple AI agents with different investment strategies
- Real-time stock analysis and trading signals
- Backtesting capabilities
- Docker support for easy deployment
- Configurable parameters for trading and analysis

## Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose
- API keys for:
  - OpenAI
  - Anthropic
  - Google AI
  - Alpha Vantage (for stock data)

## Installation


1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file from the example:
```bash
cp .env.example .env
```

3. Edit the `.env` file to add your API keys:
```env
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key
LUNARCRUSH_API_KEY=your_lunarcrush_api_key
GROQ_API_KEY=your-groq-api-key
DEEPSEEK_API_KEY=your-deepseek-api-key
```

## Usage


### Command Line Options

- `--cryptos`: Comma-separated list of crypto symbols (e.g., BTC,ETH,SOL)
- `--show-reasoning`: Show reasoning from each agent

### Running using Python

To run the main program:
```bash
python -m src.main --cryptos BTC,ETH,SOL
```



