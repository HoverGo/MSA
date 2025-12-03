# Быстрый старт

## Запуск проекта

### 1. Запуск через Docker Compose

```bash
docker-compose up --build
```

Это запустит все 4 микросервиса:
- API Gateway: http://localhost:8000
- Auth Service: http://localhost:8001
- Data Service: http://localhost:8002
- Logging Service: http://localhost:8003

### 2. Проверка работы

Откройте в браузере:
- API Gateway Swagger: http://localhost:8000/docs
- Auth Service Swagger: http://localhost:8001/docs

Или используйте скрипт для тестирования:

```bash
# Linux/Mac
chmod +x scripts/quick_test.sh
./scripts/quick_test.sh

# Windows PowerShell
.\scripts\quick_test.ps1
```

### 3. Быстрый тест

```bash
# Получение JWT токена
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

## Тестовые пользователи

- **Администратор:**
  - Username: `admin`
  - Password: `admin123`

- **Обычный пользователь:**
  - Username: `user`
  - Password: `user123`

## Полные примеры

Запустите полный набор примеров:

```bash
cd examples
python requests_examples.py
```

Или curl примеры:

```bash
chmod +x examples/curl_examples.sh
./examples/curl_examples.sh
```

## Документация API

Все сервисы имеют автоматически сгенерированную документацию Swagger:
- API Gateway: http://localhost:8000/docs
- Auth Service: http://localhost:8001/docs
- Data Service: http://localhost:8002/docs
- Logging Service: http://localhost:8003/docs

