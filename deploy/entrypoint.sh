#!/bin/sh
# 打包部署（容器启动脚本）由 deepseekv4pro 生成
set -e

cd /app/backend

if [ ! -f "vector_store/chroma.sqlite3" ] || [ "${REBUILD_KB:-0}" = "1" ]; then
    echo "[init] 正在构建知识库向量（首次约 1~2 分钟）..."
    python 04_build_kb.py
fi

echo "[init] 启动服务..."
exec python 06_web_app.py
