# PortfolioMind

PortfolioMind 是一个智能投资组合分析和管理系统，提供投资组合分析、风险评估和投资建议等功能。

## 系统架构

系统由以下主要组件组成：

1. **FastAPI 后端服务** (`jsonrpc/`)
   - 提供 JSON-RPC API 接口
   - 处理投资组合分析请求
   - 管理用户偏好和投资建议

2. **Go 客户端服务** (`src/`)
   - 处理用户请求
   - 与 FastAPI 后端通信
   - 提供用户界面和交互

## 快速开始

### 环境要求

- Python 3.8+
- Go 1.16+
- MongoDB 4.4+
- Docker (可选)

### 安装依赖

1. 安装 Python 依赖：
```bash
pip install -r requirements.txt
```

2. 安装 Go 依赖：
```bash
go mod download
```

### 配置

1. 创建 `.env` 文件并配置必要的环境变量：
```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB=portfoliomind
```

2. 配置 API 密钥（在 `config.py` 中）：
```python
API_KEYS = {
    "your_api_key": "your_secret"
}
```

### 启动服务

1. 启动 FastAPI 后端服务：
```bash
# Windows
python jsonrpc/run.py

# Linux/WSL2
python3 jsonrpc/run.py
```

2. 启动 Go 客户端服务：
```bash
# 在 WSL2 中运行
go run src/main.go
```

## API 文档

### 投资组合分析接口

#### 1. 分析投资组合

```http
POST /model
Content-Type: application/json

{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "analyze_portfolio",
    "params": {
        "address": "user_address",
        "show_reasoning": true
    }
}
```

响应示例：
```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": [
        {
            "token": "SUT",
            "usd": 400.0
        },
        {
            "token": "FARTCOIN",
            "usd": 350.0
        },
        {
            "token": "TRUMP",
            "usd": 250.0
        }
    ]
}
```

#### 2. 获取投资建议

```http
POST /model
Content-Type: application/json

{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "get_investment_advice",
    "params": {
        "address": "user_address",
    }
}
```

响应示例：
```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "TKX": {
            "investment_amount": 400.0
        },
        "SUT": {
            "investment_amount": 350.0
        },
        "VIRTUAL": {
            "investment_amount": 250.0
        }
    }
}
```

### 健康检查接口

```http
GET /health
```

响应示例：
```json
{
    "status": "healthy",
    "mongodb": "connected"
}
```

## 开发指南

### 项目结构

```
portfoliomind/
├── jsonrpc/              # FastAPI 后端服务
│   ├── routes/          # API 路由
│   ├── services/        # 业务逻辑
│   └── server.py        # 服务器配置
├── src/                 # Go 客户端服务
│   ├── main.go         # 主程序
│   └── handlers/       # 请求处理器
└── tests/              # 测试文件
```

### 添加新功能

1. 在 `jsonrpc/routes/` 中添加新的路由
2. 在 `jsonrpc/services/` 中实现业务逻辑
3. 在 `src/handlers/` 中添加对应的客户端处理

### 测试

运行 Python 测试：
```bash
pytest tests/
```

运行 Go 测试：
```bash
go test ./...
```

## 故障排除

### 常见问题

1. **连接被拒绝**
   - 检查 FastAPI 服务是否正在运行
   - 确认端口 8000 未被占用
   - 检查防火墙设置

2. **MongoDB 连接错误**
   - 确认 MongoDB 服务正在运行
   - 检查连接字符串是否正确
   - 验证数据库用户权限

3. **API 认证错误**
   - 检查 API 密钥配置
   - 确认请求头中包含正确的认证信息

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License


