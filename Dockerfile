FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置 PYTHONPATH 确保可以导入项目模块
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8080

# 启动服务器
CMD ["python", "-m", "utils.server"]
