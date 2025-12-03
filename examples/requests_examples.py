"""
Примеры запросов к микросервисам
Демонстрирует работу JWT, API ключей, HMAC, динамических токенов, rate limiting
"""
import requests
import json
import time
import hmac
import hashlib
import base64
from datetime import datetime

# Базовые URL
GATEWAY_URL = "http://localhost:8000"
AUTH_URL = f"{GATEWAY_URL}/auth"
DATA_URL = f"{GATEWAY_URL}/data"
LOGGING_URL = f"{GATEWAY_URL}/logging"

def print_response(title, response):
    """Красивый вывод ответа"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")

# ============================================
# 1. JWT Аутентификация
# ============================================
print("\n" + "="*60)
print("1. JWT АУТЕНТИФИКАЦИЯ")
print("="*60)

# Регистрация пользователя
print("\n1.1. Регистрация нового пользователя")
register_data = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
}
response = requests.post(f"{AUTH_URL}/register", json=register_data)
print_response("Регистрация", response)

# Получение JWT токена
print("\n1.2. Получение JWT токена (логин)")
login_data = {
    "username": "admin",
    "password": "admin123"
}
response = requests.post(
    f"{AUTH_URL}/token",
    data=login_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
print_response("Логин", response)
token = response.json().get("access_token")
print(f"\nJWT Token получен: {token[:50]}...")

# Проверка токена
print("\n1.3. Проверка JWT токена")
response = requests.post(
    f"{AUTH_URL}/verify-token",
    json={"token": token}
)
print_response("Проверка токена", response)

# Получение информации о текущем пользователе
print("\n1.4. Получение информации о текущем пользователе")
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{AUTH_URL}/users/me", headers=headers)
print_response("Информация о пользователе", response)

# ============================================
# 2. API Keys с HMAC
# ============================================
print("\n" + "="*60)
print("2. API КЛЮЧИ С HMAC")
print("="*60)

# Создание API ключа
print("\n2.1. Создание API ключа")
response = requests.post(
    f"{AUTH_URL}/api-keys",
    json={"name": "Test API Key", "permissions": ["read", "write"]},
    headers=headers
)
print_response("Создание API ключа", response)
api_key_data = response.json()
key_id = api_key_data.get("key_id")
secret_key = api_key_data.get("secret_key")
print(f"\nAPI Key ID: {key_id}")
print(f"Secret Key: {secret_key}")

# Создание HMAC подписи
print("\n2.2. Создание HMAC подписи для запроса")
timestamp = str(int(time.time()))
message = f"{timestamp}{key_id}"
signature = hmac.new(
    secret_key.encode(),
    message.encode(),
    hashlib.sha256
).hexdigest()
print(f"Message: {message}")
print(f"HMAC Signature: {signature}")

# Проверка API ключа с HMAC
print("\n2.3. Проверка API ключа с HMAC")
hmac_headers = {
    "X-API-Key-ID": key_id,
    "X-API-Signature": signature,
    "X-API-Timestamp": timestamp
}
response = requests.post(
    f"{AUTH_URL}/verify-api-key",
    headers=hmac_headers
)
print_response("Проверка API ключа", response)

# ============================================
# 3. Динамические токены (ZTNA)
# ============================================
print("\n" + "="*60)
print("3. ДИНАМИЧЕСКИЕ ТОКЕНЫ (ZTNA)")
print("="*60)

# Создание динамического токена
print("\n3.1. Создание динамического токена")
response = requests.post(
    f"{AUTH_URL}/dynamic-tokens",
    headers=headers
)
print_response("Создание динамического токена", response)
dynamic_token = response.json().get("token")
print(f"\nDynamic Token: {dynamic_token}")

# Проверка динамического токена
print("\n3.2. Проверка динамического токена")
response = requests.post(
    f"{AUTH_URL}/verify-dynamic-token",
    json={"token": dynamic_token}
)
print_response("Проверка динамического токена", response)

# ============================================
# 4. Работа с Data Service
# ============================================
print("\n" + "="*60)
print("4. РАБОТА С DATA SERVICE")
print("="*60)

# Создание элемента данных
print("\n4.1. Создание элемента данных")
data_item = {
    "title": "Test Item",
    "content": "This is a test content"
}
response = requests.post(
    f"{DATA_URL}/data",
    json=data_item,
    headers=headers
)
print_response("Создание элемента", response)
item_id = response.json().get("id")

# Получение всех элементов
print("\n4.2. Получение всех элементов данных")
response = requests.get(f"{DATA_URL}/data", headers=headers)
print_response("Получение всех элементов", response)

# Получение конкретного элемента
print(f"\n4.3. Получение элемента с ID {item_id}")
response = requests.get(f"{DATA_URL}/data/{item_id}", headers=headers)
print_response("Получение элемента", response)

# Обновление элемента
print(f"\n4.4. Обновление элемента с ID {item_id}")
update_data = {
    "title": "Updated Test Item",
    "content": "This is updated content"
}
response = requests.put(
    f"{DATA_URL}/data/{item_id}",
    json=update_data,
    headers=headers
)
print_response("Обновление элемента", response)

# ============================================
# 5. Rate Limiting
# ============================================
print("\n" + "="*60)
print("5. RATE LIMITING")
print("="*60)

print("\n5.1. Множественные запросы для проверки rate limiting")
print("Отправка 10 запросов подряд...")
blocked_count = 0
for i in range(10):
    response = requests.get(f"{GATEWAY_URL}/health")
    if response.status_code == 429:
        blocked_count += 1
        print(f"  Запрос {i+1}: Блокирован (429 Too Many Requests)")
    else:
        print(f"  Запрос {i+1}: OK ({response.status_code})")
    time.sleep(0.1)

print(f"\nИтого заблокировано: {blocked_count} запросов")

# ============================================
# 6. Логирование и аудит
# ============================================
print("\n" + "="*60)
print("6. ЛОГИРОВАНИЕ И АУДИТ")
print("="*60)

# Получение логов
print("\n6.1. Получение последних логов")
response = requests.get(f"{LOGGING_URL}/logs?limit=5")
print_response("Получение логов", response)

# Статистика логов
print("\n6.2. Получение статистики логов")
response = requests.get(f"{LOGGING_URL}/logs/stats")
print_response("Статистика", response)

# ============================================
# 7. Проверка ролей (Admin vs User)
# ============================================
print("\n" + "="*60)
print("7. ПРОВЕРКА РОЛЕЙ")
print("="*60)

# Логин как обычный пользователь
print("\n7.1. Логин как обычный пользователь")
user_login = {
    "username": "user",
    "password": "user123"
}
response = requests.post(
    f"{AUTH_URL}/token",
    data=user_login,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)
user_token = response.json().get("access_token")
user_headers = {"Authorization": f"Bearer {user_token}"}
print_response("Логин пользователя", response)

# Попытка удалить элемент (только для админов)
print(f"\n7.2. Попытка удалить элемент (обычный пользователь - должно быть запрещено)")
response = requests.delete(
    f"{DATA_URL}/data/{item_id}",
    headers=user_headers
)
print_response("Попытка удаления (пользователь)", response)

# Удаление элемента как админ
print(f"\n7.3. Удаление элемента как админ")
response = requests.delete(
    f"{DATA_URL}/data/{item_id}",
    headers=headers  # Используем токен админа
)
print_response("Удаление элемента (админ)", response)

print("\n" + "="*60)
print("ВСЕ ПРИМЕРЫ ЗАВЕРШЕНЫ")
print("="*60)

