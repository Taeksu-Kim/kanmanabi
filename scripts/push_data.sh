#!/usr/bin/env bash
# 로컬 data/ 산출물을 운영 DB(EC2)에 적재한다.
#
# PostgreSQL 5432는 외부에 열지 않으므로 SSH 터널을 거친다. 터널 열기 →
# 비밀번호 조회 → DATABASE_URL 조립 → seed 실행을 한 번에 처리하고,
# 끝나면 터널을 정리한다.
#
# 사용:
#   bash scripts/push_data.sh EP44          # 특정 EP만 증분 적재 (평소)
#   bash scripts/push_data.sh EP44,EP45     # 여러 EP
#   bash scripts/push_data.sh --rebuild     # 전체 재구축 (초기 구축 전용, 확인 받음)
#   bash scripts/push_data.sh --check       # 적재 없이 현재 DB 상태만 확인
set -euo pipefail

EC2_HOST="${EC2_HOST:-43.200.123.0}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/t4g.pem}"
LOCAL_PORT="${LOCAL_PORT:-15432}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ARG="${1:-}"
if [ -z "$ARG" ]; then
  sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
  exit 1
fi
[ -f "$SSH_KEY" ] || { echo "SSH 키가 없다: $SSH_KEY"; exit 1; }

echo "── EC2에서 DB 비밀번호 조회"
PGPW=$(ssh -i "$SSH_KEY" -o ConnectTimeout=15 "ubuntu@$EC2_HOST" \
       'grep POSTGRES_PASSWORD ~/kanmanabi/.env | cut -d= -f2')
[ -n "$PGPW" ] || { echo "비밀번호를 읽지 못했다 (~/kanmanabi/.env 확인)"; exit 1; }

if (echo > "/dev/tcp/127.0.0.1/$LOCAL_PORT") 2>/dev/null; then
  echo "── 터널 재사용 (localhost:$LOCAL_PORT 이미 열려 있음)"
else
  echo "── SSH 터널 (localhost:$LOCAL_PORT → EC2 5432)"
  ssh -i "$SSH_KEY" -N -L "$LOCAL_PORT:127.0.0.1:5432" "ubuntu@$EC2_HOST" &
  TUNNEL_PID=$!
  trap 'kill $TUNNEL_PID 2>/dev/null || true' EXIT     # 스크립트가 어떻게 끝나든 정리
  for i in $(seq 1 20); do
    (echo > "/dev/tcp/127.0.0.1/$LOCAL_PORT") 2>/dev/null && break
    sleep 0.5
  done
fi

export DATABASE_URL="postgresql+psycopg://korean:${PGPW}@localhost:${LOCAL_PORT}/korean_helper"
export PYTHONPATH="$ROOT/backend:$ROOT/scripts"

status() {
  python3 - <<'PY'
from app.db import SessionLocal
from app import models
db = SessionLocal()
eps = db.query(models.Episode).count()
qs = db.query(models.Question).count()
vs = db.query(models.Vocab).count()
novid = db.query(models.Episode).filter(models.Episode.youtube_id.is_(None)).count()
print(f"   episodes {eps} (youtube_id 없음 {novid}) / questions {qs} / vocab {vs}")
PY
}

echo "── 적재 전 상태"; status

case "$ARG" in
  --check)
    echo "확인만 수행했다."; exit 0 ;;
  --rebuild)
    echo
    echo "⚠️  전체 재구축은 questions id를 재발급한다."
    echo "    유저 SRS 진도(ReviewCard)가 무효화되고, 진도가 있으면 FK 때문에 실패한다."
    read -r -p "    계속하려면 'rebuild' 입력: " confirm
    [ "$confirm" = "rebuild" ] || { echo "취소했다."; exit 1; }
    python3 "$ROOT/scripts/seed.py" --rebuild ;;
  *)
    python3 "$ROOT/scripts/seed.py" --episodes "$ARG" ;;
esac

echo "── 적재 후 상태"; status
echo "완료. 서버 재배포는 필요 없다 (API가 DB를 직접 읽는다)."
