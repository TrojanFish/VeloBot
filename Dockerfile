FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# 安装系统依赖 (如果需要)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 创建非 root 用户
RUN useradd -m botuser && chown -R botuser:botuser /app
USER botuser

# 复制项目文件
# 注意：在模块化后，这里可能需要复制整个 src# 复制项目文件
COPY --chown=botuser:botuser main.py .
COPY --chown=botuser:botuser src/ ./src/

# 创建数据目录
RUN mkdir -p /app/data

EXPOSE 5000

# 启动命令
CMD ["python", "-u", "main.py"]
