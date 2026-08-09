#!/usr/bin/env bash
# EC2에서 실행되는 배포 스크립트. SSM Run Command(root)가 호출한다.
#
# git은 ubuntu 사용자로 돌린다 — root로 pull하면 파일 소유자가 root가 되어
# 이후 ubuntu의 git 작업이 깨지고, safe.directory 경고도 난다.
# docker는 root로 그대로 실행한다.
set -euo pipefail

APP_DIR=/home/ubuntu/kanmanabi
cd "$APP_DIR"

echo "── git pull (as ubuntu)"
runuser -u ubuntu -- git -C "$APP_DIR" pull --ff-only

echo "── compose up (rebuild)"
docker compose up -d --build

echo "── migration"
docker compose exec -T backend alembic upgrade head

echo "── health"
for i in $(seq 1 10); do
  if curl -fsS localhost:8000/api/health; then echo; break; fi
  echo "  대기 $i/10"; sleep 3
done

docker compose ps --format 'table {{.Service}}\t{{.Status}}'
