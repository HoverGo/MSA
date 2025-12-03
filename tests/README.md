# Тесты безопасности и проникновения

Набор тестов для проверки безопасности, уязвимостей и взаимодействия микросервисов.

## Доступные тесты

### 1. security_tests.py
**Комплексные тесты безопасности**
- Валидация JWT токенов
- Rate Limiting
- WAF защита
- Контроль доступа на основе ролей
- API ключи и HMAC
- ZTNA токены
- Защита от brute force
- Валидация входных данных

**Запуск:**
```bash
cd tests
python security_tests.py
```

### 2. penetration_tests.py
**Тесты на проникновение**
- SQL Injection
- XSS атаки
- Path Traversal
- Манипуляция JWT
- IDOR (Insecure Direct Object Reference)
- Защита от Brute Force
- CSRF
- Information Disclosure
- DoS защита

**Запуск:**
```bash
cd tests
python penetration_tests.py
```

### 3. integration_tests.py
**Интеграционные тесты**
- Проверка здоровья сервисов
- Поток Auth → Data Service
- Маршрутизация через Gateway
- Интеграция с Logging Service
- Распространение JWT между сервисами
- Контроль доступа на основе ролей
- Конкурентные запросы
- Обработка ошибок

**Запуск:**
```bash
cd tests
python integration_tests.py
```

### 4. load_test.py
**Нагрузочное тестирование**
- Rate Limiting под нагрузкой
- Нагрузка на Auth Service
- Нагрузка на Data Service
- Производительность Gateway
- Устойчивая нагрузка

**Запуск:**
```bash
cd tests
python load_test.py
```

### 5. vulnerability_scanner.py
**Автоматическое сканирование уязвимостей**
- Сканирование security headers
- Проверка эндпоинтов
- Анализ механизмов аутентификации
- Проверка CORS настроек
- Поиск утечки чувствительных данных
- Анализ безопасности JWT

**Запуск:**
```bash
cd tests
python vulnerability_scanner.py
```

Генерирует отчёт в `vulnerability_report.json`

## Запуск всех тестов

### Windows PowerShell
```powershell
cd tests
python security_tests.py
python penetration_tests.py
python integration_tests.py
python load_test.py
python vulnerability_scanner.py
```

### Linux/Mac
```bash
cd tests
python3 security_tests.py
python3 penetration_tests.py
python3 integration_tests.py
python3 load_test.py
python3 vulnerability_scanner.py
```

## Скрипт для запуска всех тестов

Создайте файл `run_all_tests.sh` (Linux/Mac) или `run_all_tests.ps1` (Windows):

### Linux/Mac
```bash
#!/bin/bash
cd tests
echo "=== Security Tests ==="
python3 security_tests.py
echo -e "\n=== Penetration Tests ==="
python3 penetration_tests.py
echo -e "\n=== Integration Tests ==="
python3 integration_tests.py
echo -e "\n=== Load Tests ==="
python3 load_test.py
echo -e "\n=== Vulnerability Scanner ==="
python3 vulnerability_scanner.py
```

### Windows PowerShell
```powershell
cd tests
Write-Host "=== Security Tests ==="
python security_tests.py
Write-Host "`n=== Penetration Tests ==="
python penetration_tests.py
Write-Host "`n=== Integration Tests ==="
python integration_tests.py
Write-Host "`n=== Load Tests ==="
python load_test.py
Write-Host "`n=== Vulnerability Scanner ==="
python vulnerability_scanner.py
```

## Требования

Все тесты требуют:
- Python 3.8+
- Библиотека `requests`
- Запущенные микросервисы (через `docker-compose up`)

Установка зависимостей:
```bash
pip install requests
```

## Интерпретация результатов

### Security Tests
- **PASS**: Механизм безопасности работает корректно
- **FAIL**: Обнаружена проблема в защите

### Penetration Tests
- **CRITICAL**: Критическая уязвимость, требует немедленного исправления
- **HIGH**: Высокая уязвимость, рекомендуется исправить в ближайшее время
- **MEDIUM**: Средняя уязвимость, стоит рассмотреть исправление
- **WARNING**: Предупреждение, не критично

### Integration Tests
- Проверяет корректность взаимодействия между сервисами
- Высокий процент успешных тестов = стабильная система

### Load Tests
- **RPS**: Запросов в секунду
- **Response Time**: Время ответа (среднее, перцентили)
- **Success Rate**: Процент успешных запросов

### Vulnerability Scanner
- Генерирует JSON отчёт со всеми найденными проблемами
- Рекомендуется периодически запускать для мониторинга безопасности

## Рекомендации

1. **Регулярное тестирование**: Запускайте тесты после каждого значительного изменения
2. **CI/CD интеграция**: Добавьте тесты в pipeline автоматизации
3. **Мониторинг**: Используйте результаты тестов для отслеживания состояния безопасности
4. **Исправление уязвимостей**: Приоритизируйте исправление CRITICAL и HIGH уязвимостей

