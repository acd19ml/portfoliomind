# PortfolioMind System

## Installation & Startup

### 1. Install Dependencies (Python)

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Start the Services (Locally)

```bash
# Start both Chat and JSONRPC services using the unified runner
python run_servers.py

# Or, start them individually (in separate terminals):
python chat/run.py
python jsonrpc/run.py
```

### 3. Start with Docker

```bash
# Build and run all services with Docker Compose
# (Make sure your .env file is configured if needed)
docker-compose up --build
```

---

## System Architecture

```
┌──────────────────────────────┐
│        React Frontend        │
│   (react frontend server)    │
└─────────────┬────────────────┘
              │ HTTP (3000)
              ▼
┌──────────────────────────────┐
│        Go Backend Server     │
│     (go backend server)      │
│  Listen: 0.0.0.0:8080        │
│ 1. Receives frontend requests│
│ 2. Calls Chat Service        │
│ 3. Calls JSONRPC Service     │
└───────┬─────────┬────────────┘
        │         │
        ▼         ▼
┌──────────────────────────────┐      ┌──────────────────────────────┐
│         Chat Service         │      │      JSONRPC Service         │
│ (chat/server.py, FastAPI)    │      │ (jsonrpc/server.py, FastAPI) │
│ Listen: 0.0.0.0:8008         │      │ Listen: 0.0.0.0:8000         │
└─────────────┬────────────────┘      └─────────────┬────────────────┘
              │                                     │
              ▼                                     ▼
┌──────────────────────────────┐      ┌──────────────────────────────┐
│       chat/tools.py          │      │         MongoDB              │
│  (internal tool, requests    │      │ (public or container)        │
│   JSONRPC Service)           │      └──────────────────────────────┘
└──────────────────────────────┘
```

### Component Descriptions

- **React Frontend**: Provides the user interface. All user actions are sent to the Go backend via HTTP requests. *(Note: The React frontend service is not included in this repository.)*
- **Go Backend Server**: Acts as a middle layer between the frontend and Python services. Handles business aggregation, permission checks, and forwards requests to the Chat and JSONRPC services. *(Note: The Go backend service is not included in this repository.)*
- **Chat Service**: Handles natural language conversations and streaming AI responses. Internally uses `chat/tools.py` to request analysis from the JSONRPC service.
- **JSONRPC Service**: Handles investment analysis, portfolio analysis, and other business logic. Directly accesses MongoDB for data storage and retrieval.
- **MongoDB**: Stores all business data.

### Agent Implementation

- The core agent logic, including analyst orchestration and business analysis, is implemented in the `src` directory of this repository.

### Typical Request Flow

1. The user initiates an action in the React frontend.
2. The Go backend receives the request and, based on business logic, forwards it to the Chat or JSONRPC service.
3. If the Chat service needs analysis, it uses `chat/tools.py` to request the JSONRPC service.
4. The JSONRPC service processes the analysis request, accesses MongoDB for data, and returns the result.
5. The Go backend returns the result to the frontend, which displays it to the user.

---

## Project Structure

- `src/` - Core agent implementation logic (analyst orchestration, business analysis etc.)
- `chat/` - Python Chat service (FastAPI)
- `jsonrpc/` - Python JSONRPC service (FastAPI)
- `run_servers.py` - Unified entry to run both Python services
- `config.py` - Centralized configuration
- `README.md` - Project documentation

> **Note:** The Go backend and React frontend services are not included in this repository.

## Deployment

- All services can be containerized using Docker.
- MongoDB can be a public instance or a container.
- Environment variables (such as `MONGODB_URI`) should be set for correct service connectivity.

## Prediction and Recommendation Results
![image](https://github.com/user-attachments/assets/82d4a7cc-c22c-4fb8-ad29-fee31fb9c35a)
![image](https://github.com/user-attachments/assets/ee435344-3569-47b6-a016-d03aadbba95d)


## Contact

For more information, please refer to the source code or contact the maintainers.


