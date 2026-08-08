# 로컬 품질 게이트. GitHub Actions 대신 병합 전 개발자가 직접 실행한다.
set shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

backend_dir := "concenews-backend"
test_database_url := "postgresql+psycopg://concenews:concenews@localhost:5433/concenews_test"

default:
    @just --list

# 린트 검사
check-ruff:
    cd {{backend_dir}}; uv run ruff check src tests

# 정적 타입 검사
check-ty:
    cd {{backend_dir}}; uv run ty check src

# 모듈 경계(import-linter) 검사
check-imports:
    cd {{backend_dir}}; uv run lint-imports

# 외부 의존성 없는 빠른 회귀 검사
check-unit:
    cd {{backend_dir}}; uv run pytest tests/unit -q

# 테스트용 PostgreSQL을 일시 기동해 통합 테스트를 실행하고 항상 정리한다.
check-integration:
    $project_root = $PWD; $started = $false; try { docker compose --project-name concenews-test -f "$project_root\\docker-compose.test.yml" up -d --wait; if ($LASTEXITCODE -ne 0) { throw "테스트 데이터베이스 기동에 실패했습니다." }; $started = $true; $env:DATABASE_URL = "{{test_database_url}}"; Set-Location "$project_root\\{{backend_dir}}"; uv run pytest tests/integration -q -m "not e2e" --ignore=spikes; if ($LASTEXITCODE -ne 0) { throw "통합 테스트에 실패했습니다." } } finally { if ($started) { docker compose --project-name concenews-test -f "$project_root\\docker-compose.test.yml" down } }

# 실제 외부 API와 테스트용 PostgreSQL을 함께 검증한다. API 토큰이 필요하며 병합 전 게이트에는 포함하지 않는다.
check-e2e:
    $project_root = $PWD; $started = $false; try { if (-not $env:THENEWSAPI_TOKEN) { throw "THENEWSAPI_TOKEN 환경 변수가 필요합니다." }; docker compose --project-name concenews-test -f "$project_root\\docker-compose.test.yml" up -d --wait; if ($LASTEXITCODE -ne 0) { throw "테스트 데이터베이스 기동에 실패했습니다." }; $started = $true; $env:DATABASE_URL = "{{test_database_url}}"; Set-Location "$project_root\\{{backend_dir}}"; uv run pytest tests/integration -q -m e2e --ignore=spikes; if ($LASTEXITCODE -ne 0) { throw "E2E 테스트에 실패했습니다." } } finally { if ($started) { docker compose --project-name concenews-test -f "$project_root\\docker-compose.test.yml" down } }

# 병합 전 전체 품질 게이트. 모든 하위 작업이 성공해야 한다.
check-branch-green: check-ruff check-ty check-imports check-unit check-integration
