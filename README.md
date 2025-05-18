# PortfolioMind

PortfolioMind 是一个基于 AI 的加密货币投资组合分析系统，使用 WebSocket 进行实时进度更新和模型调用。

## 功能特点

- 实时进度更新：通过 WebSocket 实时显示分析进度
- 多分析师支持：集成多个 AI 分析师进行综合分析
- 风险管理系统：自动评估和管理投资风险
- 实时市场数据：集成实时加密货币市场数据
- 可扩展架构：支持添加新的分析师和模型

## 系统架构

系统由以下主要组件组成：

1. **WebSocket 服务器**
   - `/ws/progress` 端点：处理进度更新订阅
   - `/ws/model` 端点：处理模型调用请求

2. **进度更新机制**
   - 实时状态更新：显示每个分析师的工作状态
   - 进度广播：向所有订阅者广播更新
   - 心跳机制：保持连接活跃

3. **分析系统**
   - 多分析师工作流
   - 风险管理系统 （待实现）
   - 投资组合优化 （待实现）

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/portfoliomind.git
cd portfoliomind
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，添加必要的 API 密钥
```

## 使用方法

1. 启动服务器：
```bash
python -m jsonrpc.server
```

2. 运行客户端：
```bash
python -m cryptomcp.client.main
```

3. 分析投资组合：
```python
from cryptomcp.client.main import PortfolioAnalysisClient

async def analyze():
    client = PortfolioAnalysisClient()
    await client.connect()
    result = await client.analyze_portfolio(["BTC", "ETH"])
    print(result)
    await client.close()
```

## 进度更新

系统提供实时进度更新，包括：

- 分析师状态：显示每个分析师的工作状态
- 加密货币分析：显示当前正在分析的加密货币
- 完成状态：显示分析完成的百分比
- 错误报告：实时显示任何错误或警告

## 开发

### 添加新的分析师

1. 在 `src/agents` 目录下创建新的分析师模块
2. 实现必要的接口
3. 在 `src/utils/analysts.py` 中注册分析师

### 添加新的模型

1. 在 `src/llm/models.py` 中添加新的模型配置
2. 实现模型接口
3. 更新模型选择逻辑

## 贡献

欢迎提交 Pull Request 和 Issue。

## 许可证

MIT License

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



