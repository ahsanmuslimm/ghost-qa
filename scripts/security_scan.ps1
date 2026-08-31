# Ghost QA — local security audit
# Runs the same checks CI performs: static analysis + dependency vulnerabilities.
#
#   pip install -r requirements-dev.txt
#   .\scripts\security_scan.ps1

$ErrorActionPreference = "Continue"
$failed = $false

Write-Host "`n=== [1/2] Bandit (static analysis, medium+ severity) ===" -ForegroundColor Cyan
python -m bandit -r app -ll -ii --exclude tests,frontend,loadtests
if ($LASTEXITCODE -ne 0) { $failed = $true }

Write-Host "`n=== [2/2] pip-audit (dependency vulnerabilities) ===" -ForegroundColor Cyan
python -m pip_audit -r requirements.txt --strict
if ($LASTEXITCODE -ne 0) { $failed = $true }

if ($failed) {
    Write-Host "`nSecurity scan finished with findings — review the output above." -ForegroundColor Yellow
    exit 1
}
Write-Host "`nSecurity scan passed with no blocking findings." -ForegroundColor Green
