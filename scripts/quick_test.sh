#!/bin/bash

# Быстрый тест всех сервисов

echo "======================================"
echo "Быстрый тест микросервисов"
echo "======================================"

GATEWAY_URL="http://localhost:8000"

# Проверка здоровья API Gateway
echo -e "\n1. Проверка API Gateway..."
curl -s "${GATEWAY_URL}/health" | jq '.' || echo "API Gateway недоступен"

# Получение токена
echo -e "\n2. Получение JWT токена..."
TOKEN_RESPONSE=$(curl -s -X POST "${GATEWAY_URL}/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123")

TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
    echo "✓ Токен получен"
    echo "Token: ${TOKEN:0:50}..."
    
    # Тест запроса к Data Service
    echo -e "\n3. Тест запроса к Data Service..."
    curl -s -X GET "${GATEWAY_URL}/data/data" \
      -H "Authorization: Bearer $TOKEN" | jq '.' || echo "Ошибка запроса"
else
    echo "✗ Не удалось получить токен"
    echo "Response: $TOKEN_RESPONSE"
fi

# Проверка сервисов
echo -e "\n4. Статус сервисов..."
curl -s "${GATEWAY_URL}/services" | jq '.'

echo -e "\n======================================"
echo "Тест завершён"
echo "======================================"

