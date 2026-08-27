# Phase 1 smoke test: DEMO_MODE end-to-end pipeline
$ErrorActionPreference = "Stop"
$base = "http://127.0.0.1:8123"

Write-Host "== 1. Valid webhook =="
$prNum = Get-Random -Minimum 1000 -Maximum 99999
$body = (Get-Content -Raw smoke_payload.json) -replace '"number": 77', ('"number": ' + $prNum) -replace '"sha": "smoke123"', ('"sha": "smoke' + $prNum + '"')
$r = Invoke-RestMethod -Uri "$base/api/webhooks/github" -Method Post -Body $body -ContentType "application/json" -Headers @{"X-GitHub-Event"="pull_request"}
Write-Host ($r | ConvertTo-Json -Compress)
if ($r.status -ne "pipeline_started") { throw "Expected pipeline_started, got $($r.status)" }
$runId = $r.pipeline_run_id

Write-Host "== 2. Malformed payload rejected (400) =="
try {
    $bad = '{"action":"opened","pull_request":{"number":0,"title":"x"}}'
    Invoke-WebRequest -Uri "$base/api/webhooks/github" -Method Post -Body $bad -ContentType "application/json" -Headers @{"X-GitHub-Event"="pull_request"} | Out-Null
    throw "Malformed payload was NOT rejected"
} catch [System.Net.WebException] {
    $code = [int]$_.Exception.Response.StatusCode
    if ($code -ne 400) { throw "Expected 400, got $code" }
    Write-Host "Rejected with 400 as expected"
}

Write-Host "== 3. Wait for background pipeline =="
Start-Sleep -Seconds 6

Write-Host "== 3b. Mint JWT =="
$token = python -c "import jwt, time; print(jwt.encode({'sub':'admin@ghost.qa','role':'approver','exp':int(time.time())+3600,'iat':int(time.time())},'change-me-in-production',algorithm='HS256'))"
$auth = @{ "Authorization" = "Bearer $token" }
Write-Host "Token acquired"

Write-Host "== 4. Run detail =="
$run = Invoke-RestMethod -Uri "$base/api/runs/$runId" -Headers $auth
Write-Host ("status=" + $run.status + " risk=" + $run.risk_level)

Write-Host "== 5. Tests generated =="
$tests = Invoke-RestMethod -Uri "$base/api/runs/$runId/tests" -Headers $auth
$count = if ($tests.tests) { @($tests.tests).Count } else { @($tests).Count }
Write-Host ("test count: " + $count)
if ($count -lt 1) { throw "No test cases generated" }

Write-Host "== 6. Risk report =="
$report = Invoke-RestMethod -Uri "$base/api/runs/$runId/report" -Headers $auth
Write-Host ("risk=" + $report.risk_level + " passed=" + $report.passed + " failed=" + $report.failed)

Write-Host "SMOKE TEST PASSED"
