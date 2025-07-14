# 使用官方 Python 运行时作为父镜像
FROM registry.labition.com/prod/python:3.11-slim

# 设置工作目录
WORKDIR /app

# 将当前目录内容复制到位于 /app 中的容器中
COPY . /app

# 安装 requirements.txt 中指定的任何所需包
RUN pip install --no-cache-dir -r requirements.txt -i http://mirrors.aliyun.com/pypi/simple --trusted-host mirrors.aliyun.com

# 使得9001端口可以从 Docker 容器外部访问
EXPOSE 9001

# 运行 main.py 时容器启动

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]