#!/bin/bash

# Примеры curl запросов для тестирования микросервисов
# Запустите все сервисы через docker-compose перед выполнением

GATEWAY_URL="http://localhost:8000"
AUTH_URL="${GATEWAY_URL}/auth"
DATA_URL="${GATEWAY_URL}/data"

echo "======================================"
echo "Примеры curl запросов к микросервисам"
echo "======================================"

# 1. Health check
echo -e "\n1. Health Check API Gateway"
curl -X GET "${GATEWAY_URL}/health" | jq

# 2. Регистрация пользователя
echo -e "\n2. Регистрация пользователя"
curl -X POST "${AUTH_URL}/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
  }' | jq

# 3. Получение JWT токена
echo -e "\n3. Получение JWT токена"
TOKEN_RESPONSE=$(curl -s -X POST "${AUTH_URL}/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123")
TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')
echo $TOKEN_RESPONSE | jq
echo "Token: ${TOKEN:0:50}..."

# 4. Проверка токена
echo -e "\n4. Проверка JWT токена"
curl -X POST "${AUTH_URL}/verify-token" \
  -H "Content-Type: application/json" \
  -d "{\"token\": \"$TOKEN\"}" | jq

# 5. Получение информации о пользователе
echo -e "\n5. Информация о текущем пользователе"
curl -X GET "${AUTH_URL}/users/me" \
  -H "Authorization: Bearer $TOKEN" | jq

# 6. Создание API ключа
echo -e "\n6. Создание API ключа"
API_KEY_RESPONSE=$(curl -s -X POST "${AUTH_URL}/api-keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test API Key",
    "permissions": ["read", "write"]
  }')
KEY_ID=$(echo $API_KEY_RESPONSE | jq -r '.key_id')
SECRET_KEY=$(echo $API_KEY_RESPONSE | jq -r '.secret_key')
echo $API_KEY_RESPONSE | jq

# 7. Создание элемента данных
echo -e "\n7. Создание элемента данных"
ITEM_RESPONSE=$(curl -s -X POST "${DATA_URL}/data" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Item",
    "content": "Test content"
  }')
ITEM_ID=$(echo $ITEM_RESPONSE | jq -r '.id')
echo $ITEM_RESPONSE | jq

# 8. Получение всех элементов
echo -e "\n8. Получение всех элементов данных"
curl -X GET "${DATA_URL}/data" \
  -H "Authorization: Bearer $TOKEN" | jq

# 9. Получение конкретного элемента
echo -e "\n9. Получение элемента с ID $ITEM_ID"
curl -X GET "${DATA_URL}/data/$ITEM_ID" \
  -H "Authorization: Bearer $TOKEN" | jq

# 10. Rate Limiting - множественные запросы
echo -e "\n10. Тест Rate Limiting (10 запросов)"
for i in {1..10}; do
  echo -n "  Запрос $i: "
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${GATEWAY_URL}/health")
  echo "Status $STATUS"
  sleep 0.2
done

# 11. Логи
echo -e "\n11. Получение логов"
curl -X GET "${GATEWAY_URL}/logging/logs?limit=5" | jq

# 12. Статистика
echo -e "\n12. Статистика логов"
curl -X GET "${GATEWAY_URL}/logging/logs/stats" | jq

echo -e "\n======================================"
echo "Все примеры выполнены"
echo "======================================"

