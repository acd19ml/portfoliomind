# 使用 Python 3.13 作为基础镜像
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
COPY src/ src/
COPY jsonrpc/ jsonrpc/
COPY chat/ chat/
COPY config.py .
COPY run_servers.py .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 8000 8008

# 启动服务
CMD ["python", "run_servers.py"] 