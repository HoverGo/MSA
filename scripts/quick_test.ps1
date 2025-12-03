# PowerShell скрипт для быстрого тестирования

$GATEWAY_URL = "http://localhost:8000"

Write-Host "======================================"
Write-Host "Быстрый тест микросервисов"
Write-Host "======================================"

# Проверка здоровья API Gateway
Write-Host "`n1. Проверка API Gateway..."
try {
    $health = Invoke-RestMethod -Uri "$GATEWAY_URL/health" -Method Get
    Write-Host "✓ API Gateway доступен"
    $health | ConvertTo-Json
} catch {
    Write-Host "✗ API Gateway недоступен: $_"
}

# Получение токена
Write-Host "`n2. Получение JWT токена..."
try {
    $body = @{
        username = "admin"
        password = "admin123"
    }
    
    $tokenResponse = Invoke-RestMethod -Uri "$GATEWAY_URL/auth/token" `
        -Method Post `
        -ContentType "application/x-www-form-urlencoded" `
        -Body $body
    
    $token = $tokenResponse.access_token
    
    if ($token) {
        Write-Host "✓ Токен получен"
        Write-Host "Token: $($token.Substring(0, [Math]::Min(50, $token.Length)))..."
        
        # Тест запроса к Data Service
        Write-Host "`n3. Тест запроса к Data Service..."
        $headers = @{
            Authorization = "Bearer $token"
        }
        
        try {
            $data = Invoke-RestMethod -Uri "$GATEWAY_URL/data/data" `
                -Method Get `
                -Headers $headers
            Write-Host "✓ Данные получены"
            $data | ConvertTo-Json
        } catch {
            Write-Host "✗ Ошибка запроса: $_"
        }
    }
} catch {
    Write-Host "✗ Не удалось получить токен: $_"
}

# Проверка сервисов
Write-Host "`n4. Статус сервисов..."
try {
    $services = Invoke-RestMethod -Uri "$GATEWAY_URL/services" -Method Get
    $services | ConvertTo-Json
} catch {
    Write-Host "✗ Ошибка получения статуса сервисов: $_"
}

Write-Host "`n======================================"
Write-Host "Тест завершён"
Write-Host "======================================"

