$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$projectName = "concenews-container-test"
$composeFiles = @(
    "-f", "$projectRoot\docker-compose.yml",
    "-f", "$projectRoot\docker-compose.container-test.yml"
)

function Invoke-Compose {
    & docker compose --project-name $projectName @composeFiles @args
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose 명령이 실패했습니다: $args"
    }
}

try {
    Invoke-Compose config --quiet
    Invoke-Compose build
    Invoke-Compose up -d postgres migrate api

    $healthUrl = "http://localhost:18000/health"
    $deadline = (Get-Date).AddSeconds(30)
    $response = $null
    do {
        try {
            $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                break
            }
        } catch {
            Start-Sleep -Seconds 1
        }
    } while ((Get-Date) -lt $deadline)

    if ($null -eq $response -or $response.StatusCode -ne 200) {
        throw "API 컨테이너가 30초 안에 정상 기동하지 않았습니다."
    }

    Invoke-Compose run --rm --no-deps scheduler sh -c 'rm -f /tmp/scheduler-ready; python -m scripts.scheduler_smoke >/tmp/scheduler.log 2>&1 & process_id=$!; attempt=0; while [ ! -f /tmp/scheduler-ready ] && [ $attempt -lt 30 ]; do sleep 1; attempt=$((attempt + 1)); done; test -f /tmp/scheduler-ready; kill -TERM $process_id; wait $process_id'
} finally {
    & docker compose --project-name $projectName @composeFiles down --volumes --remove-orphans
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "컨테이너 smoke 정리에 실패했습니다."
    }
}
