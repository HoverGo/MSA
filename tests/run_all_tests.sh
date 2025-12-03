#!/bin/bash

# Скрипт для запуска всех тестов безопасности

echo "======================================"
echo "ЗАПУСК ВСЕХ ТЕСТОВ БЕЗОПАСНОСТИ"
echo "======================================"

cd "$(dirname "$0")"

echo -e "\n[1/5] Запуск Security Tests..."
python3 security_tests.py

echo -e "\n[2/5] Запуск Penetration Tests..."
python3 penetration_tests.py

echo -e "\n[3/5] Запуск Integration Tests..."
python3 integration_tests.py

echo -e "\n[4/5] Запуск Load Tests..."
python3 load_test.py

echo -e "\n[5/5] Запуск Vulnerability Scanner..."
python3 vulnerability_scanner.py

echo -e "\n======================================"
echo "ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ"
echo "======================================"
echo "Проверьте результаты выше и файл vulnerability_report.json"

