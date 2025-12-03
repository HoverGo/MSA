# Описание реализации

## Реализованные технологии и методы безопасности

### 1. JWT авторизация и аутентификация ✅

**Реализация:**
- Auth Service (`auth-service/app/main.py`) предоставляет эндпоинты:
  - `POST /auth/token` - получение JWT токена (OAuth2 password flow)
  - `POST /auth/verify-token` - проверка валидности токена
  - `GET /auth/users/me` - получение информации о текущем пользователе
  
- JWT токены содержат:
  - `sub` - username пользователя
  - `role` - роль пользователя (admin/user/readonly)
  - `exp` - время истечения (30 минут)
  
- API Gateway проверяет JWT токены перед маршрутизацией к защищённым сервисам

**Файлы:**
- `auth-service/app/utils.py` - функции создания и проверки JWT
- `data-service/app/utils.py` - проверка токенов через Auth Service

### 2. API Gateway с маршрутизацией ✅

**Реализация:**
- API Gateway (`api-gateway/app/main.py`) является единой точкой входа
- Проксирует запросы к микросервисам по паттерну: `/{service}/{path}`
- Поддерживаемые сервисы: `auth`, `data`, `logging`
- Маршрутизация с учётом доступности сервисов через Service Mesh

**Файлы:**
- `api-gateway/app/main.py` - основной файл с маршрутизацией
- `api-gateway/app/utils/service_mesh.py` - упрощённая имитация Service Mesh

### 3. Rate Limiting ✅

**Реализация:**
- Ограничение: 5 запросов в секунду на IP адрес
- Используется библиотека `slowapi`
- При превышении лимита возвращается HTTP 429 (Too Many Requests)
- Настроено на уровне API Gateway для всех запросов

**Файлы:**
- `api-gateway/app/main.py` - декоратор `@limiter.limit("5/second")`
- `api-gateway/app/utils/rate_limiter.py` - дополнительный in-memory rate limiter

### 4. Service Mesh (упрощённая имитация) ✅

**Реализация:**
- Класс `ServiceMesh` проверяет доступность сервисов
- Кеширование статуса здоровья сервисов (30 секунд)
- Методы:
  - `check_health(url)` - проверка здоровья сервиса
  - `is_service_available(name)` - проверка доступности с кешированием

**Файлы:**
- `api-gateway/app/utils/service_mesh.py`

### 5. TLS/HTTPS ✅

**Реализация:**
- Поддержка HTTPS через uvicorn с SSL сертификатами
- Скрипты для генерации самоподписанных сертификатов:
  - `scripts/generate_certs.sh` - для Linux/Mac
  - `scripts/generate_certs.ps1` - для Windows
- Сертификаты хранятся в директории `certs/`
- API Gateway может запускаться с HTTPS (закомментировано для простоты демонстрации)

**Файлы:**
- `api-gateway/Dockerfile` - настройка HTTPS
- `scripts/generate_certs.sh` / `scripts/generate_certs.ps1`

### 6. API ключи + HMAC ✅

**Реализация:**
- Auth Service предоставляет эндпоинты для управления API ключами:
  - `POST /auth/api-keys` - создание API ключа (возвращает key_id и secret_key)
  - `GET /auth/api-keys` - список API ключей пользователя
  - `POST /auth/verify-api-key` - проверка API ключа с HMAC подписью

- HMAC подпись:
  - Использует SHA-256
  - Подпись включает timestamp для защиты от replay атак
  - Проверка временного окна (5 минут)

**Файлы:**
- `auth-service/app/main.py` - эндпоинты для API ключей
- `auth-service/app/utils.py` - функции генерации и проверки HMAC
- `auth-service/app/models.py` - модель APIKey

**Пример использования:**
```python
# Генерация подписи
timestamp = str(int(time.time()))
message = f"{timestamp}{key_id}"
signature = hmac.new(
    secret_key.encode(),
    message.encode(),
    hashlib.sha256
).hexdigest()
```

### 7. WAF (Web Application Firewall) ✅

**Реализация:**
- Middleware `WAFMiddleware` проверяет все входящие запросы
- Блокирует подозрительные паттерны:
  - XSS атаки: `<script`, `javascript:`, `onerror=`
  - SQL injection: `SELECT.*FROM`, `DROP.*TABLE`, `UNION.*SELECT`
- Проверка URL, тела запроса и заголовков
- При обнаружении блокирует запрос с HTTP 403

**Файлы:**
- `api-gateway/app/middleware/waf.py`
- `api-gateway/app/config.py` - настройки заблокированных паттернов

### 8. ZTNA + динамические токены ✅

**Реализация:**
- Динамические токены создаются через Auth Service:
  - `POST /auth/dynamic-tokens` - создание токена (действителен 60 минут)
  - `POST /auth/verify-dynamic-token` - проверка токена
- ZTNA Middleware проверяет наличие токена в заголовке `X-ZTNA-Token`
- Токены имеют ограниченное время жизни
- Автоматическая деактивация истёкших токенов

**Файлы:**
- `auth-service/app/main.py` - эндпоинты для динамических токенов
- `auth-service/app/models.py` - модель DynamicToken
- `api-gateway/app/middleware/ztna.py` - ZTNA middleware

### 9. Логирование и аудит ✅

**Реализация:**
- Logging Service (`logging-service/`) хранит все логи запросов
- API Gateway автоматически логирует все проксированные запросы
- Логи содержат:
  - Сервис, эндпоинт, метод
  - Информация о пользователе (ID, роль)
  - IP адрес, User-Agent
  - Тела запроса и ответа
  - Время выполнения
  - HTTP статус код

- Эндпоинты Logging Service:
  - `POST /logging/logs` - создание записи лога
  - `GET /logging/logs` - получение логов с фильтрацией
  - `GET /logging/logs/stats` - статистика по логам

**Файлы:**
- `logging-service/app/main.py` - основные эндпоинты
- `logging-service/app/models.py` - модель AuditLog
- `api-gateway/app/middleware/logging.py` - отправка логов

## Архитектура микросервисов

### Взаимодействие между сервисами

```
Client → API Gateway → Auth Service
                ↓
          Data Service (проверка JWT через Auth Service)
                ↓
          Logging Service (логирование всех запросов)
```

### Базы данных

- **Auth Service**: SQLite (`auth.db`) - пользователи, API ключи, динамические токены
- **Data Service**: SQLite (`data.db`) - элементы данных
- **Logging Service**: SQLite (`logs.db`) - логи запросов

### Сеть Docker

Все сервисы общаются через внутреннюю Docker сеть `microservices-network`:
- Внутренние URL: `http://auth-service:8001`, `http://data-service:8002`, и т.д.
- Внешние порты: 8000 (Gateway), 8001 (Auth), 8002 (Data), 8003 (Logging)

## Структура кода

Каждый микросервис имеет следующую структуру:
```
service-name/
├── app/
│   ├── main.py       # Основной файл FastAPI приложения
│   ├── models.py     # SQLAlchemy модели
│   ├── schemas.py    # Pydantic схемы для валидации
│   ├── utils.py      # Вспомогательные функции
│   └── database.py   # Настройка БД
├── Dockerfile        # Docker образ
└── requirements.txt  # Зависимости Python
```

## Тестирование

### Примеры использования

1. **Python скрипт** (`examples/requests_examples.py`):
   - Полный набор примеров для всех функций
   - Демонстрирует JWT, API ключи, HMAC, динамические токены
   - Тестирует rate limiting и проверку ролей

2. **curl скрипт** (`examples/curl_examples.sh`):
   - Примеры команд curl для всех эндпоинтов
   - Подходит для быстрого тестирования

3. **Быстрый тест** (`scripts/quick_test.sh` / `scripts/quick_test.ps1`):
   - Минимальный набор проверок работоспособности

### Swagger UI

Все сервисы имеют автоматически сгенерированную документацию:
- Доступна по адресу `/docs` каждого сервиса
- Позволяет интерактивное тестирование API

## Запуск проекта

```bash
# 1. Генерация сертификатов (опционально)
./scripts/generate_certs.sh

# 2. Запуск всех сервисов
docker-compose up --build

# 3. Проверка работы
curl http://localhost:8000/health
```

## Заключение

Все требуемые технологии безопасности реализованы и интегрированы в микросервисную архитектуру. Проект готов для демонстрации и использования в рамках курсовой работы.

