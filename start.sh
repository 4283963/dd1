#!/usr/bin/env bash
set -e

echo "===== 海洋牧场水质监控系统 - 启动脚本 ====="

if ! command -v psql &> /dev/null; then
  echo "错误: 未找到 psql，请先安装 PostgreSQL"
  exit 1
fi

DB_NAME="seawater"
DB_USER="${PGUSER:-postgres}"
DB_HOST="${PGHOST:-localhost}"
DB_PORT="${PGPORT:-5432}"

echo "[1/4] 检查数据库..."
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
  echo "  创建数据库 $DB_NAME ..."
  createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
else
  echo "  数据库 $DB_NAME 已存在"
fi

echo "[2/4] 初始化表结构..."
cd backend
pip install -q -r requirements.txt 2>/dev/null
python -c "from app.database import engine, Base; from app.models import SeaWaterData; Base.metadata.create_all(bind=engine); print('  表结构创建完成')"

echo "[3/4] 填充测试数据..."
python seed.py

echo "[4/4] 启动后端服务..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

cd ../frontend
echo "  启动前端服务..."
npx vite --host 0.0.0.0 --port 3000 &
FRONTEND_PID=$!

echo ""
echo "===== 启动完成 ====="
echo "  前端: http://localhost:3000"
echo "  后端: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
