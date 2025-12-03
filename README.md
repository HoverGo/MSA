# Микросервисная архитектура с безопасностью (MSA)

Курсовая работа - набор микросервисов на Python с FastAPI, демонстрирующий различные технологии и методы безопасности.

## Архитектура

Проект включает следующие микросервисы:

1. **API Gateway** (порт 8000) - центральная точка входа
   - Маршрутизация запросов
   - Rate limiting (5 запросов/секунду)
   - WAF (Web Application Firewall)
   - ZTNA (Zero Trust Network Access)
   - Проверка JWT токенов
   - Логирование всех запросов

2. **Auth Service** (порт 8001) - аутентификация и авторизация
   - JWT токены
   - Регистрация и аутентификация пользователей
   - Роли пользователей (admin, user, readonly)
   - API ключи с HMAC подписью
   - Динамические токены для ZTNA

3. **Data Service** (порт 8002) - управление данными
   - CRUD операции с данными
   - Проверка прав доступа через JWT
   - Разделение доступа по ролям

4. **Logging Service** (порт 8003) - логирование и аудит
   - Хранение логов всех запросов
   - Статистика и фильтрация логов
   - Аудит активности пользователей

## Технологии безопасности

- ✅ **JWT авторизация и аутентификация** - токены для доступа к сервисам
- ✅ **API Gateway** - маршрутизация и защита на уровне шлюза
- ✅ **Rate Limiting** - ограничение количества запросов
- ✅ **Service Mesh** - упрощённая имитация для маршрутизации
- ✅ **TLS/HTTPS** - поддержка HTTPS (требует настройки сертификатов)
- ✅ **API ключи + HMAC** - подпись запросов с использованием HMAC
- ✅ **WAF** - защита от XSS, SQL injection и других атак
- ✅ **ZTNA + динамические токены** - Zero Trust Network Access
- ✅ **Логирование и аудит** - полное логирование всех запросов

## Установка и запуск

### Требования

- Docker и Docker Compose
- Python 3.11+ (для запуска примеров)
- OpenSSL (для генерации сертификатов TLS)

### Запуск через Docker Compose

1. Клонируйте репозиторий или скопируйте файлы

2. (Опционально) Сгенерируйте TLS сертификаты:
```bash
# Linux/Mac
chmod +x scripts/generate_certs.sh
./scripts/generate_certs.sh

# Windows PowerShell
.\scripts\generate_certs.ps1
```

3. Запустите все сервисы:
```bash
docker-compose up --build
```

4. Проверьте, что все сервисы запущены:
```bash
curl http://localhost:8000/health
```

### Тестовые данные

После запуска доступны следующие тестовые пользователи:

- **Администратор:**
  - Username: `admin`
  - Password: `admin123`
  - Role: `admin`

- **Обычный пользователь:**
  - Username: `user`
  - Password: `user123`
  - Role: `user`

## Использование

### Примеры запросов

#### 1. Python скрипт (полный набор примеров)

```bash
cd examples
python requests_examples.py
```

Этот скрипт демонстрирует:
- Регистрацию и аутентификацию
- Работу с JWT токенами
- API ключи с HMAC
- Динамические токены (ZTNA)
- Работу с данными
- Rate limiting
- Проверку ролей

#### 2. curl примеры

```bash
chmod +x examples/curl_examples.sh
./examples/curl_examples.sh
```

### Ручное тестирование

#### Получение JWT токена

```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Ответ:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

#### Использование токена

```bash
TOKEN="ваш_токен_здесь"

curl -X GET "http://localhost:8000/data/data" \
  -H "Authorization: Bearer $TOKEN"
```

#### Создание API ключа с HMAC

```bash
# Создание ключа
curl -X POST "http://localhost:8000/auth/api-keys" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My API Key", "permissions": ["read"]}'

# Использование ключа с HMAC подписью
# (см. examples/requests_examples.py для деталей реализации)
```

#### Создание динамического токена (ZTNA)

```bash
curl -X POST "http://localhost:8000/auth/dynamic-tokens" \
  -H "Authorization: Bearer $TOKEN"
```

## Структура проекта

```
MSA/
├── api-gateway/          # API Gateway сервис
│   ├── app/
│   │   ├── main.py       # Основной файл
│   │   ├── middleware/   # WAF, ZTNA middleware
│   │   ├── utils/        # Rate limiter, Service Mesh
│   │   └── config.py     # Конфигурация
│   ├── Dockerfile
│   └── requirements.txt
├── auth-service/         # Сервис аутентификации
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py     # SQLAlchemy модели
│   │   ├── schemas.py    # Pydantic схемы
│   │   ├── utils.py      # JWT, HMAC утилиты
│   │   └── database.py
│   ├── Dockerfile
│   └── requirements.txt
├── data-service/         # Сервис данных
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── utils.py
│   ├── Dockerfile
│   └── requirements.txt
├── logging-service/      # Сервис логирования
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── Dockerfile
│   └── requirements.txt
├── examples/             # Примеры использования
│   ├── requests_examples.py
│   └── curl_examples.sh
├── scripts/              # Вспомогательные скрипты
│   ├── generate_certs.sh
│   └── generate_certs.ps1
├── docker-compose.yml    # Docker Compose конфигурация
└── README.md
```

## API Endpoints

### API Gateway

- `GET /health` - проверка здоровья
- `GET /services` - список сервисов и их статус
- `GET /{service}/{path}` - проксирование запросов к сервисам

### Auth Service

- `POST /auth/register` - регистрация пользователя
- `POST /auth/token` - получение JWT токена
- `POST /auth/verify-token` - проверка токена
- `GET /auth/users/me` - информация о текущем пользователе
- `POST /auth/api-keys` - создание API ключа
- `GET /auth/api-keys` - список API ключей
- `POST /auth/verify-api-key` - проверка API ключа с HMAC
- `POST /auth/dynamic-tokens` - создание динамического токена
- `POST /auth/verify-dynamic-token` - проверка динамического токена

### Data Service

- `GET /data/data` - получение всех элементов
- `GET /data/data/{id}` - получение элемента по ID
- `POST /data/data` - создание элемента
- `PUT /data/data/{id}` - обновление элемента
- `DELETE /data/data/{id}` - удаление элемента (только админы)

### Logging Service

- `POST /logging/logs` - создание записи лога
- `GET /logging/logs` - получение логов с фильтрацией
- `GET /logging/logs/stats` - статистика по логам

Все сервисы также имеют Swagger UI доступный по адресу `/docs`

## Особенности реализации

### Rate Limiting
- Ограничение: 5 запросов в секунду на IP адрес
- Используется библиотека `slowapi`
- При превышении лимита возвращается HTTP 429

### WAF
- Блокировка подозрительных паттернов:
  - XSS атаки (`<script`, `javascript:`)
  - SQL injection (`SELECT`, `DROP TABLE`)
  - Другие опасные паттерны

### Service Mesh
- Упрощённая имитация через проверку здоровья сервисов
- Кеширование статуса сервисов
- Маршрутизация с учётом доступности

### JWT
- Токены действительны 30 минут
- Содержат информацию о пользователе и роли
- Проверяются на каждом защищённом эндпоинте

### HMAC
- Используется SHA-256 для подписи
- Подпись включает timestamp для защиты от replay атак
- Проверка временного окна (5 минут)

### ZTNA
- Динамические токены с ограниченным временем жизни
- Проверка токенов через Auth Service
- Дополнительный уровень безопасности

## Тестирование безопасности

Проект включает комплексный набор тестов для проверки безопасности:

### Доступные тесты

1. **security_tests.py** - Комплексные тесты безопасности
   - JWT валидация, Rate Limiting, WAF, RBAC, HMAC, ZTNA

2. **penetration_tests.py** - Тесты на проникновение
   - SQL Injection, XSS, Path Traversal, JWT манипуляция, IDOR, DoS

3. **integration_tests.py** - Интеграционные тесты
   - Проверка взаимодействия между сервисами

4. **load_test.py** - Нагрузочное тестирование
   - Проверка производительности и устойчивости под нагрузкой

5. **vulnerability_scanner.py** - Автоматическое сканирование уязвимостей
   - Анализ security headers, CORS, JWT, утечек данных

### Запуск тестов

```bash
cd tests

# Запуск всех тестов
./run_all_tests.sh  # Linux/Mac
.\run_all_tests.ps1  # Windows

# Или по отдельности
python security_tests.py
python penetration_tests.py
python integration_tests.py
python load_test.py
python vulnerability_scanner.py
```

Подробнее в [tests/README.md](tests/README.md)

## Разработка

### Локальная разработка

Для запуска сервисов локально без Docker:

```bash
# Auth Service
cd auth-service
pip install -r requirements.txt
uvicorn app.main:app --port 8001

# Data Service
cd data-service
pip install -r requirements.txt
uvicorn app.main:app --port 8002

# Logging Service
cd logging-service
pip install -r requirements.txt
uvicorn app.main:app --port 8003

# API Gateway
cd api-gateway
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

### Переменные окружения

Создайте `.env` файл для настройки:

```env
AUTH_SERVICE_URL=http://auth-service:8001
DATA_SERVICE_URL=http://data-service:8002
LOGGING_SERVICE_URL=http://logging-service:8003
SECRET_KEY=your-secret-key-here
```

## Безопасность в production

⚠️ **Важно:** Это демонстрационный проект для курсовой работы. Для production использования необходимо:

1. Использовать настоящие TLS сертификаты от доверенного CA
2. Хранить секретные ключи в безопасном хранилище (например, HashiCorp Vault)
3. Настроить правильные CORS политики
4. Использовать более строгие настройки rate limiting
5. Добавить мониторинг и алертинг
6. Настроить резервное копирование баз данных
7. Использовать PostgreSQL вместо SQLite для production
8. Настроить правильные политики безопасности контейнеров

## Лицензия

Этот проект создан для образовательных целей в рамках курсовой работы.

## Автор

Создано для курсовой работы по микросервисной архитектуре и безопасности.

