#!/bin/sh
# 打包部署（一键部署脚本）由 deepseekv4pro 生成
set -e

if ! command -v docker >/dev/null 2>&1; then
    echo "[1/3] 安装 Docker..."
    curl -fsSL https://get.docker.com | sh
fi

if ! docker compose version >/dev/null 2>&1; then
    echo "[2/3] 安装 docker compose 插件..."
    apt-get update && apt-get install -y docker-compose-plugin
fi

echo "[3/3] 构建并启动服务..."
docker compose up -d --build

echo ""
echo "========== 启动完成 =========="
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo "浏览器访问：http://${IP}/"
echo "查看状态：  docker compose ps"
echo "查看日志：  docker compose logs -f app"
