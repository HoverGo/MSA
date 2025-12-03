# PowerShell скрипт для запуска всех тестов безопасности

Write-Host "======================================"
Write-Host "ЗАПУСК ВСЕХ ТЕСТОВ БЕЗОПАСНОСТИ"
Write-Host "======================================"

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "`n[1/5] Запуск Security Tests..."
python security_tests.py

Write-Host "`n[2/5] Запуск Penetration Tests..."
python penetration_tests.py

Write-Host "`n[3/5] Запуск Integration Tests..."
python integration_tests.py

Write-Host "`n[4/5] Запуск Load Tests..."
python load_test.py

Write-Host "`n[5/5] Запуск Vulnerability Scanner..."
python vulnerability_scanner.py

Write-Host "`n======================================"
Write-Host "ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ"
Write-Host "======================================"
Write-Host "Проверьте результаты выше и файл vulnerability_report.json"

