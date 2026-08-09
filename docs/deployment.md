# 배포 가이드 (AWS)

> 인프라 사양·제약은 [`../contexts/aws_deployment_context.md`](../contexts/aws_deployment_context.md).
> 이 문서는 **실제로 실행할 순서**만 담는다. 콘솔 작업과 명령어를 구분해 표기했다.

```text
CloudFront (https://xxxx.cloudfront.net)
  ├── /*      → S3        정적 프론트 (빌드 산출물)
  └── /api/*  → EC2:8000  백엔드 (Docker Compose)
                 └── PostgreSQL 컨테이너 (외부 노출 금지)
```

프론트와 API가 **같은 오리진**이라 세션 쿠키가 그대로 동작하고 CORS 설정이 필요 없다.
프론트 코드는 전부 상대경로(`/api/...`)를 쓰므로 배포용 코드 수정이 없다.

---

## 0. 배포 전 체크리스트

이 셋 중 하나라도 빠지면 **인증이 무력화되거나 로그인이 깨진다.**

- [ ] `AUTH_REQUIRED=true` — 빠뜨리면 로그인 없이 dev 스텁 유저로 전체 데이터 접근 가능
- [ ] `SESSION_SECRET` 새 랜덤값 — 기본값 그대로면 쿠키를 위조할 수 있다
- [ ] `COOKIE_SECURE=true` + `ALLOWED_ORIGINS`에 CloudFront 도메인

---

## 1. EC2 최초 셋업 (1회)

SSH 접속 후:

```bash
# Docker (Ubuntu 24.04 ARM64)
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-v2 git
sudo usermod -aG docker $USER && exec su -l $USER   # 그룹 반영

git clone https://github.com/Taeksu-Kim/kanmanabi.git ~/kanmanabi
cd ~/kanmanabi
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"   # SESSION_SECRET 값 생성
nano .env
```

`.env`에 채울 값:

```bash
POSTGRES_USER=korean
POSTGRES_PASSWORD=<강한 비밀번호>
POSTGRES_DB=korean_helper
DATABASE_URL=postgresql+psycopg://korean:<위와 동일>@db:5432/korean_helper

GOOGLE_CLIENT_ID=438365955018-....apps.googleusercontent.com
SESSION_SECRET=<위에서 생성한 값>
AUTH_REQUIRED=true
COOKIE_SECURE=true
ALLOWED_ORIGINS=https://<distribution>.cloudfront.net
```

```bash
docker compose up -d --build
docker compose exec -T backend alembic upgrade head
curl localhost:8000/api/health        # {"status":"ok"}
```

이 시점엔 DB가 비어 있다(문항 0건). 적재는 3단계.

## 2. 보안그룹

- `22` : 개발자 IP `/32` (기존 유지)
- `8000` : **CloudFront에서만** 접근 가능하도록 제한
  - 정석은 관리형 프리픽스 리스트 `com.amazonaws.global.cloudfront.origin-facing`을 소스로 지정
  - 이렇게 하면 EC2 공인 IP를 직접 때려도 CloudFront를 우회할 수 없다
- `5432` : **열지 않는다.** compose가 `127.0.0.1:5432`로만 바인딩한다

## 3. 데이터 적재 (SSH 터널)

어휘 10,198 + 문항 24,996은 로컬 `data/` 산출물에서 넣는다. **5432를 열지 않고** 터널로 한다.

```bash
# 터미널 A — 터널 유지
ssh -N -L 15432:127.0.0.1:5432 ubuntu@<EC2-IP>

# 터미널 B — 로컬 데이터로 EC2 DB에 적재
export DATABASE_URL="postgresql+psycopg://korean:<비밀번호>@localhost:15432/korean_helper"
python scripts/seed.py
```

문항을 다시 생성했을 때도 같은 방법으로 재적재한다.
(GitHub Actions는 `data/`를 갖고 있지 않아 이 단계를 대신할 수 없다.)

## 4. S3 + CloudFront

**`bash scripts/aws_setup.sh` 한 번이면 아래가 전부 생성된다**(멱등). 콘솔로 하려면 이어지는 표를 참고.

### 생성된 리소스 (2026-08-09)

| 항목 | 값 |
|---|---|
| CloudFront 도메인 | `https://d2go3igmacuzm3.cloudfront.net` |
| 배포 ID | `E1LTLHFB7EWBLT` |
| S3 버킷 | `kanmanabi-frontend-323205069978` |
| Elastic IP | `43.200.123.0` (EC2 고정) |

### 콘솔로 할 경우

**S3**
- 버킷 생성(ap-northeast-2), **퍼블릭 액세스 차단 유지**
- 정적 웹사이트 호스팅 불필요 — CloudFront가 OAC로 직접 읽는다

**CloudFront 배포**
- Origin 1: S3 버킷 (**OAC** 사용, 생성 시 버킷 정책 자동 반영)
- Origin 2: EC2 퍼블릭 IP/DNS, 프로토콜 **HTTP only**, 포트 `8000`
- 동작(Behavior) 2개:

| 경로 | Origin | 캐시 | 허용 메서드 | 전달 |
|---|---|---|---|---|
| `/api/*` | EC2 | **CachingDisabled** | GET,HEAD,OPTIONS,PUT,POST,PATCH,DELETE | **AllViewer**(쿠키·헤더·쿼리 전부) |
| `/*` (기본) | S3 | CachingOptimized | GET,HEAD | — |

> `/api/*`에서 캐시를 끄지 않으면 CloudFront가 `/api/study/next` 응답을 캐싱해
> **모든 사용자에게 같은 문제가 나간다.** 쿠키를 전달하지 않으면 로그인이 아예 안 된다.
> 이 구조에서 가장 흔한 사고 지점이다.

- **SPA fallback은 오류 페이지가 아니라 CloudFront Function으로 한다.**
  사용자 지정 오류 페이지(403/404 → index.html)는 **배포 전역**이라 `/api/*`의 403·404까지
  HTML 200으로 바꿔버린다 — API 오류가 사라져 프론트가 404를 구분하지 못한다.
  대신 viewer-request 함수에서 `/api/`로 시작하거나 확장자가 있으면 통과, 나머지만
  `/index.html`로 재작성한다(`scripts/aws_setup.sh`가 자동 생성).
- Viewer protocol policy: Redirect HTTP to HTTPS

## 5. 도메인 확정 후 (3곳 동시)

CloudFront 도메인(`https://xxxx.cloudfront.net`)이 나오면 **세 곳을 함께** 갱신한다.
하나라도 빠지면 로그인이 실패한다.

1. Google 콘솔 → 승인된 JavaScript 원본에 **추가**(localhost는 지우지 않아도 된다)
2. EC2 `.env`의 `ALLOWED_ORIGINS` → `docker compose up -d`
3. GitHub → Settings → Secrets and variables → Actions
   - Secrets: `VITE_GOOGLE_CLIENT_ID`, `AWS_DEPLOY_ROLE_ARN`
   - Variables: `S3_BUCKET`, `CLOUDFRONT_DISTRIBUTION_ID`

Google OAuth 동의 화면이 **테스트 상태**면 등록된 테스트 사용자만 로그인된다.
실사용자를 받으려면 `프로덕션으로 게시`가 필요하다(기본 스코프만 쓰므로 심사 없음).

## 6. CI/CD

| 워크플로 | 트리거 | 내용 |
|---|---|---|
| `ci.yml` | push/PR | 백엔드 pytest + 프론트 lint·typecheck·test·build |
| `deploy-frontend.yml` | `frontend/**` push | build → S3 sync → CloudFront 무효화 (OIDC) |
| `deploy-backend.yml` | 수동만 | SSH로 git pull + compose 재빌드 + 마이그레이션 |

프론트 배포는 `index.html`만 `no-cache`, 나머지 자산은 `immutable`로 올린다.
`index.html`을 캐시하면 배포해도 사용자가 옛 번들을 계속 받는다.

**백엔드 자동 배포는 아직 안 된다.** SSH 22가 개발자 IP `/32`로 제한돼 있어 Actions 러너에서
닿지 않는다. 당분간은 EC2에 직접 접속해서:

```bash
cd ~/kanmanabi && git pull --ff-only
docker compose up -d --build
docker compose exec -T backend alembic upgrade head
```

자동화하려면 러너 IP를 보안그룹에 한시적으로 열거나 SSM Session Manager를 도입해야 한다.
SSM 쪽이 SSH를 아예 닫을 수 있어 더 낫지만 IAM 역할 설정이 늘어난다.

## 7. 배포 후 확인

```bash
curl https://xxxx.cloudfront.net/api/health                    # {"status":"ok"}
curl -i https://xxxx.cloudfront.net/api/me                     # 401 (AUTH_REQUIRED=true 확인)
curl -i https://xxxx.cloudfront.net/learn/vocabulary           # 200 + index.html (SPA fallback)
```

- `/api/me`가 **200이면 인증이 무력화된 것**이다 — `AUTH_REQUIRED`를 확인한다
- 브라우저에서 로그인 → 개발자도구 Application → Cookies에 `kh_session`(HttpOnly, Secure) 확인
