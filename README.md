# PortfolioMind

PortfolioMind is an AI-powered cryptocurrency portfolio analysis system that provides real-time progress updates and model invocation using WebSocket technology.

## Features

- Real-time progress updates via WebSocket
- Multiple AI analysts for comprehensive analysis
- Automated risk management system
- Integration with real-time cryptocurrency market data
- Extensible architecture for adding new analysts and models
- Backtesting capabilities
- Docker support for easy deployment
- Configurable parameters for trading and analysis

## System Architecture

The system consists of the following main components:

1. **WebSocket Server**
   - `/ws/progress` endpoint: Handles progress update subscriptions
   - `/ws/model` endpoint: Handles model invocation requests

2. **Progress Update Mechanism**
   - Real-time status updates for each analyst
   - Broadcasts progress to all subscribers
   - Heartbeat mechanism to keep connections alive

3. **Analysis System**
   - Multi-analyst workflow
   - Automated risk management (in development)
   - Portfolio optimization (in development)

## Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose (optional)
- API keys for:
  - OpenAI
  - Anthropic
  - Google AI
  - LunarCrush
  - Groq
  - DeepSeek

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/acd19ml/portfoliomind.git
   cd portfoliomind
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file from the example:
   ```bash
   cp .env.example .env
   # Edit the .env file to add your API keys
   ```

   Example `.env` variables:
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

### Running the Main Program

To run the main program:
```bash
python -m src.main --cryptos BTC,ETH,SOL
```

### Using the Client in Python

```python
from cryptomcp.client.main import PortfolioAnalysisClient

async def analyze():
    client = PortfolioAnalysisClient()
    await client.connect()
    result = await client.analyze_portfolio(["BTC", "ETH"])
    print(result)
    await client.close()
```

## Development

### Adding a New Analyst

1. Create a new analyst module in `src/agents`.
2. Implement the required interfaces.
3. Register the analyst in `src/utils/analysts.py`.

### Adding a New Model

1. Add the new model configuration in `src/llm/models.py`.
2. Implement the model interface.
3. Update the model selection logic as needed.

## Contribution

Contributions are welcome! Please submit Pull Requests and Issues.

## License

MIT License

## Progress Updates

The system provides real-time progress updates, including:

- Analyst status: Displays the status of each analyst's work
- Crypto analysis: Shows the current crypto being analyzed
- Completion status: Displays the percentage of analysis completed
- Error report: Displays any errors or warnings in real-time

## Features

- Multiple AI agents with different investment strategies
- Docker support for easy deployment
- Configurable parameters for trading and analysis

## Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose
- API keys for:
  - OpenAI
  - Anthropic
  - Google AI

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



