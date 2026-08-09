#!/usr/bin/env bash
# AWS 리소스 생성 (S3 + CloudFront + 보안그룹). 콘솔 클릭 대신 CLI로.
#
# 실행 전 확인할 것:
#   - aws configure 로 자격증명 설정됨 (ap-northeast-2)
#   - EC2가 이미 떠 있고 백엔드가 8000에서 응답함
#
# 멱등하게 짰다 — 이미 있으면 건너뛰고 기존 값을 재사용한다. 중간에 끊겨도 다시 실행하면 된다.
# 각 단계는 무엇을 만드는지 먼저 출력한다.
#
# 사용: bash scripts/aws_setup.sh
set -euo pipefail

REGION="ap-northeast-2"
EC2_ID="i-0efad0380a5320ff8"       # t4g-trial-2026-01 (ap-northeast-2)
STATE_FILE="scratchpad/aws_state.env"      # 생성된 ID 기록 (재실행 시 재사용)

mkdir -p "$(dirname "$STATE_FILE")"
touch "$STATE_FILE"
# shellcheck disable=SC1090
source "$STATE_FILE"

save() { grep -v "^$1=" "$STATE_FILE" > "$STATE_FILE.tmp" 2>/dev/null || true
         mv "$STATE_FILE.tmp" "$STATE_FILE" 2>/dev/null || true
         echo "$1=$2" >> "$STATE_FILE"; }
step() { echo; echo "── $* ──"; }

# ─────────────────────────────────────────────────────────────
step "0. 사전 확인"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "  계정: $ACCOUNT_ID / 리전: $REGION"

read -r EC2_STATE EC2_IP EC2_DNS EC2_SG <<<"$(aws ec2 describe-instances --region "$REGION" \
  --instance-ids "$EC2_ID" \
  --query 'Reservations[0].Instances[0].[State.Name,PublicIpAddress,PublicDnsName,SecurityGroups[0].GroupId]' \
  --output text)"
if [ "$EC2_STATE" != "running" ]; then
  echo "  ❌ EC2($EC2_ID)가 running이 아니다 (현재: $EC2_STATE)"; exit 1
fi
echo "  EC2: $EC2_ID ($EC2_STATE) / IP: $EC2_IP / SG: $EC2_SG"
echo "  퍼블릭 DNS: $EC2_DNS"
# CloudFront origin은 IP를 직접 받지 않아 퍼블릭 DNS를 쓴다.
# ⚠️ 인스턴스를 stop/start 하면 IP와 DNS가 모두 바뀌고 CloudFront origin이 죽는다.
#    고정하려면 Elastic IP를 붙일 것(연결돼 있으면 무료).
if [ -z "$EC2_DNS" ] || [ "$EC2_DNS" = "None" ]; then
  echo "  ❌ 퍼블릭 DNS가 없다 — 퍼블릭 IP가 할당돼 있는지 확인"; exit 1
fi

BUCKET="kanmanabi-frontend-${ACCOUNT_ID}"

# ─────────────────────────────────────────────────────────────
step "1. S3 버킷 ($BUCKET) — 퍼블릭 접근은 차단하고 CloudFront만 읽게 한다"
if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  echo "  이미 존재 → 건너뜀"
else
  aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
    --create-bucket-configuration LocationConstraint="$REGION" >/dev/null
  echo "  생성됨"
fi
aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
echo "  퍼블릭 액세스 차단 적용"

# ─────────────────────────────────────────────────────────────
step "2. Origin Access Control — CloudFront가 S3를 서명해서 읽는 수단"
if [ -z "${OAC_ID:-}" ]; then
  OAC_ID=$(aws cloudfront create-origin-access-control --origin-access-control-config \
    "Name=kanmanabi-oac,Description=kanmanabi frontend,SigningProtocol=sigv4,SigningBehavior=always,OriginAccessControlOriginType=s3" \
    --query 'OriginAccessControl.Id' --output text 2>/dev/null \
    || aws cloudfront list-origin-access-controls \
       --query "OriginAccessControlList.Items[?Name=='kanmanabi-oac'].Id | [0]" --output text)
  save OAC_ID "$OAC_ID"
fi
echo "  OAC: $OAC_ID"

# ─────────────────────────────────────────────────────────────
step "3. CloudFront 배포 — /api/*는 EC2(캐시 없음), 나머지는 S3(캐시)"
# 관리형 정책 ID (AWS 전역 고정값)
CACHE_DISABLED="4135ea2d-6df8-44a3-9df3-4b5a84be39ad"   # CachingDisabled
CACHE_OPTIMIZED="658327ea-f89d-4fab-a63d-7e88639e58f6"  # CachingOptimized
ORIGIN_ALLVIEWER="216adef6-5c7f-47e4-b989-5492eafa07d3" # AllViewer (쿠키·헤더·쿼리 전달)

if [ -z "${DIST_ID:-}" ]; then
  cat > scratchpad/cf-config.json <<JSON
{
  "CallerReference": "kanmanabi-$(date +%s)",
  "Comment": "kanmanabi",
  "Enabled": true,
  "Origins": {
    "Quantity": 2,
    "Items": [
      {
        "Id": "s3-frontend",
        "DomainName": "${BUCKET}.s3.${REGION}.amazonaws.com",
        "OriginAccessControlId": "${OAC_ID}",
        "S3OriginConfig": { "OriginAccessIdentity": "" }
      },
      {
        "Id": "ec2-backend",
        "DomainName": "${EC2_DNS}",
        "CustomOriginConfig": {
          "HTTPPort": 8000,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "http-only",
          "OriginSslProtocols": { "Quantity": 1, "Items": ["TLSv1.2"] }
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "s3-frontend",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": { "Quantity": 2, "Items": ["GET", "HEAD"],
                        "CachedMethods": { "Quantity": 2, "Items": ["GET", "HEAD"] } },
    "CachePolicyId": "${CACHE_OPTIMIZED}",
    "Compress": true
  },
  "CacheBehaviors": {
    "Quantity": 1,
    "Items": [
      {
        "PathPattern": "/api/*",
        "TargetOriginId": "ec2-backend",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": { "Quantity": 7,
          "Items": ["GET","HEAD","OPTIONS","PUT","POST","PATCH","DELETE"],
          "CachedMethods": { "Quantity": 2, "Items": ["GET","HEAD"] } },
        "CachePolicyId": "${CACHE_DISABLED}",
        "OriginRequestPolicyId": "${ORIGIN_ALLVIEWER}",
        "Compress": true
      }
    ]
  },
  "CustomErrorResponses": {
    "Quantity": 2,
    "Items": [
      { "ErrorCode": 403, "ResponsePagePath": "/index.html",
        "ResponseCode": "200", "ErrorCachingMinTTL": 0 },
      { "ErrorCode": 404, "ResponsePagePath": "/index.html",
        "ResponseCode": "200", "ErrorCachingMinTTL": 0 }
    ]
  },
  "DefaultRootObject": "index.html",
  "PriceClass": "PriceClass_200"
}
JSON
  read -r DIST_ID DIST_DOMAIN <<<"$(aws cloudfront create-distribution \
    --distribution-config "file://scratchpad/cf-config.json" \
    --query 'Distribution.[Id,DomainName]' --output text)"
  save DIST_ID "$DIST_ID"; save DIST_DOMAIN "$DIST_DOMAIN"
  echo "  생성됨 (배포 완료까지 5~15분 걸린다)"
fi
echo "  배포: $DIST_ID / 도메인: https://$DIST_DOMAIN"

# ─────────────────────────────────────────────────────────────
step "4. S3 버킷 정책 — 이 CloudFront 배포만 읽기 허용"
cat > scratchpad/bucket-policy.json <<JSON
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowCloudFrontRead",
    "Effect": "Allow",
    "Principal": { "Service": "cloudfront.amazonaws.com" },
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::${BUCKET}/*",
    "Condition": { "StringEquals": {
      "AWS:SourceArn": "arn:aws:cloudfront::${ACCOUNT_ID}:distribution/${DIST_ID}" } }
  }]
}
JSON
aws s3api put-bucket-policy --bucket "$BUCKET" --policy "file://scratchpad/bucket-policy.json"
echo "  적용됨"

# ─────────────────────────────────────────────────────────────
step "5. 보안그룹 — 8000을 CloudFront에서만 열기 (EC2 직접 접근 차단)"
PL_ID=$(aws ec2 describe-managed-prefix-lists --region "$REGION" \
  --filters "Name=prefix-list-name,Values=com.amazonaws.global.cloudfront.origin-facing" \
  --query 'PrefixLists[0].PrefixListId' --output text)
echo "  CloudFront 프리픽스 리스트: $PL_ID"
if aws ec2 authorize-security-group-ingress --region "$REGION" --group-id "$EC2_SG" \
     --ip-permissions "IpProtocol=tcp,FromPort=8000,ToPort=8000,PrefixListIds=[{PrefixListId=$PL_ID,Description=CloudFront only}]" \
     >/dev/null 2>&1; then
  echo "  8000 허용 규칙 추가됨"
else
  echo "  이미 있거나 실패 → 콘솔에서 확인 필요"
fi

# ─────────────────────────────────────────────────────────────
echo
echo "══════════════════════════════════════════"
echo " 완료. 다음 값을 설정에 반영한다:"
echo
echo "  CloudFront 도메인 : https://$DIST_DOMAIN"
echo "  S3 버킷           : $BUCKET"
echo "  배포 ID           : $DIST_ID"
echo
echo " 1) EC2 ~/kanmanabi/.env"
echo "      ALLOWED_ORIGINS=https://$DIST_DOMAIN"
echo "      AUTH_REQUIRED=true / COOKIE_SECURE=true"
echo "    → docker compose up -d"
echo " 2) Google 콘솔 승인된 JavaScript 원본에 추가"
echo "      https://$DIST_DOMAIN"
echo " 3) GitHub → Settings → Secrets and variables → Actions"
echo "      Variables: S3_BUCKET=$BUCKET"
echo "                 CLOUDFRONT_DISTRIBUTION_ID=$DIST_ID"
echo "      Secrets:   VITE_GOOGLE_CLIENT_ID=<client id>"
echo "══════════════════════════════════════════"
