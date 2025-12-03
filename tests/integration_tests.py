"""
Интеграционные тесты для проверки взаимодействия между сервисами
"""
import requests
import time
import json
from typing import Dict, List

GATEWAY_URL = "http://localhost:8000"
AUTH_URL = f"{GATEWAY_URL}/auth"
DATA_URL = f"{GATEWAY_URL}/data"
LOGGING_URL = f"{GATEWAY_URL}/logging"

class IntegrationTests:
    def __init__(self):
        self.results = []
        self.admin_token = None
        self.user_token = None
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Логирование результата теста"""
        status = "✓ PASS" if passed else "✗ FAIL"
        self.results.append({
            "test": test_name,
            "status": status,
            "passed": passed,
            "details": details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"  {details}")
    
    def get_admin_token(self):
        """Получение токена админа"""
        if not self.admin_token:
            response = requests.post(
                f"{AUTH_URL}/token",
                data={"username": "admin", "password": "admin123"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 200:
                self.admin_token = response.json().get("access_token")
        return self.admin_token
    
    def get_user_token(self):
        """Получение токена обычного пользователя"""
        if not self.user_token:
            response = requests.post(
                f"{AUTH_URL}/token",
                data={"username": "user", "password": "user123"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 200:
                self.user_token = response.json().get("access_token")
        return self.user_token
    
    def test_service_health(self):
        """Тест 1: Проверка здоровья всех сервисов"""
        print("\n=== Тест 1: Health Check ===")
        
        services = {
            "API Gateway": GATEWAY_URL,
            "Auth Service": f"{AUTH_URL.replace('/auth', '')}/health",
            "Data Service": f"{DATA_URL.replace('/data', '')}/health",
            "Logging Service": f"{LOGGING_URL}/health"
        }
        
        all_healthy = True
        for service_name, url in services.items():
            try:
                response = requests.get(url, timeout=5)
                healthy = response.status_code == 200
                self.log_test(
                    f"1.1. {service_name} доступен",
                    healthy,
                    f"Status: {response.status_code}"
                )
                if not healthy:
                    all_healthy = False
            except Exception as e:
                self.log_test(
                    f"1.1. {service_name} доступен",
                    False,
                    f"Error: {str(e)}"
                )
                all_healthy = False
        
        return all_healthy
    
    def test_auth_to_data_flow(self):
        """Тест 2: Поток от Auth Service к Data Service"""
        print("\n=== Тест 2: Auth → Data Service Flow ===")
        
        token = self.get_admin_token()
        if not token:
            self.log_test("2.1. Получение токена", False, "Could not get token")
            return False
        
        self.log_test("2.1. Получение токена", True, "Token получен")
        
        # Использование токена для доступа к Data Service
        response = requests.get(
            f"{DATA_URL}/data",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        self.log_test(
            "2.2. Доступ к Data Service с токеном",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        return response.status_code == 200
    
    def test_gateway_routing(self):
        """Тест 3: Маршрутизация через API Gateway"""
        print("\n=== Тест 3: Gateway Routing ===")
        
        # Тест маршрутизации к Auth Service
        response = requests.get(f"{GATEWAY_URL}/auth/health")
        self.log_test(
            "3.1. Маршрутизация к Auth Service",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
        
        # Тест маршрутизации к Data Service (требует токен)
        token = self.get_admin_token()
        if token:
            response = requests.get(
                f"{GATEWAY_URL}/data/data",
                headers={"Authorization": f"Bearer {token}"}
            )
            self.log_test(
                "3.2. Маршрутизация к Data Service",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        
        # Тест маршрутизации к Logging Service
        response = requests.get(f"{GATEWAY_URL}/logging/health")
        self.log_test(
            "3.3. Маршрутизация к Logging Service",
            response.status_code == 200,
            f"Status: {response.status_code}"
        )
    
    def test_logging_integration(self):
        """Тест 4: Интеграция с Logging Service"""
        print("\n=== Тест 4: Logging Integration ===")
        
        # Выполняем несколько операций
        token = self.get_admin_token()
        if token:
            # Создание элемента данных
            requests.post(
                f"{DATA_URL}/data",
                json={"title": "Test Item", "content": "Test"},
                headers={"Authorization": f"Bearer {token}"}
            )
            
            time.sleep(1)  # Даём время на логирование
            
            # Проверяем логи
            response = requests.get(f"{LOGGING_URL}/logs?limit=5")
            if response.status_code == 200:
                logs = response.json()
                recent_log = None
                for log in logs:
                    if log.get("service") == "data":
                        recent_log = log
                        break
                
                self.log_test(
                    "4.1. Логи сохраняются в Logging Service",
                    recent_log is not None,
                    f"Найдено логов: {len(logs)}"
                )
            else:
                self.log_test("4.1. Логи сохраняются", False, f"Status: {response.status_code}")
        else:
            self.log_test("4.1. Логи сохраняются", False, "Could not get token")
    
    def test_jwt_propagation(self):
        """Тест 5: Распространение JWT между сервисами"""
        print("\n=== Тест 5: JWT Propagation ===")
        
        token = self.get_admin_token()
        if not token:
            self.log_test("5.1. JWT распространение", False, "Could not get token")
            return
        
        # Проверяем, что токен валиден в Auth Service
        verify_response = requests.post(
            f"{AUTH_URL}/verify-token",
            json={"token": token}
        )
        
        if verify_response.status_code == 200:
            self.log_test("5.1. Токен валиден в Auth Service", True)
            
            # Используем токен в Data Service через Gateway
            data_response = requests.get(
                f"{DATA_URL}/data",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            self.log_test(
                "5.2. Токен работает через Gateway в Data Service",
                data_response.status_code == 200,
                f"Status: {data_response.status_code}"
            )
        else:
            self.log_test("5.1. JWT распространение", False, "Token invalid")
    
    def test_role_based_access_flow(self):
        """Тест 6: Поток контроля доступа на основе ролей"""
        print("\n=== Тест 6: Role-Based Access Flow ===")
        
        user_token = self.get_user_token()
        admin_token = self.get_admin_token()
        
        if not user_token or not admin_token:
            self.log_test("6.1. RBAC flow", False, "Could not get tokens")
            return
        
        # Обычный пользователь создаёт элемент
        create_response = requests.post(
            f"{DATA_URL}/data",
            json={"title": "User Item", "content": "User content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        if create_response.status_code == 201:
            item_id = create_response.json().get("id")
            self.log_test("6.1. Пользователь может создавать", True)
            
            # Пользователь может читать свои элементы
            read_response = requests.get(
                f"{DATA_URL}/data/{item_id}",
                headers={"Authorization": f"Bearer {user_token}"}
            )
            self.log_test(
                "6.2. Пользователь может читать свои элементы",
                read_response.status_code == 200,
                f"Status: {read_response.status_code}"
            )
            
            # Админ может удалять
            delete_response = requests.delete(
                f"{DATA_URL}/data/{item_id}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            self.log_test(
                "6.3. Админ может удалять",
                delete_response.status_code in [200, 204],
                f"Status: {delete_response.status_code}"
            )
    
    def test_concurrent_requests(self):
        """Тест 7: Конкурентные запросы"""
        print("\n=== Тест 7: Concurrent Requests ===")
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        token = self.get_admin_token()
        if not token:
            self.log_test("7.1. Конкурентные запросы", False, "Could not get token")
            return
        
        def make_request():
            try:
                response = requests.get(
                    f"{DATA_URL}/data",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5
                )
                return response.status_code
            except:
                return 0
        
        # Отправляем 10 параллельных запросов
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in as_completed(futures)]
        
        success_count = sum(1 for r in results if r == 200)
        self.log_test(
            "7.1. Конкурентные запросы обрабатываются",
            success_count >= 8,
            f"Успешно: {success_count}/10"
        )
    
    def test_error_handling(self):
        """Тест 8: Обработка ошибок между сервисами"""
        print("\n=== Тест 8: Error Handling ===")
        
        # Тест недоступного сервиса (имитация)
        # В реальности нужно остановить один из сервисов
        # Здесь просто проверяем обработку ошибок
        
        # Невалидный токен
        response = requests.get(
            f"{DATA_URL}/data",
            headers={"Authorization": "Bearer invalid_token"}
        )
        self.log_test(
            "8.1. Невалидный токен обрабатывается",
            response.status_code == 401,
            f"Status: {response.status_code}"
        )
        
        # Несуществующий ресурс
        token = self.get_admin_token()
        if token:
            response = requests.get(
                f"{DATA_URL}/data/99999",
                headers={"Authorization": f"Bearer {token}"}
            )
            self.log_test(
                "8.2. Несуществующий ресурс обрабатывается",
                response.status_code == 404,
                f"Status: {response.status_code}"
            )
    
    def run_all_tests(self):
        """Запуск всех интеграционных тестов"""
        print("=" * 60)
        print("ИНТЕГРАЦИОННЫЕ ТЕСТЫ")
        print("=" * 60)
        
        self.test_service_health()
        self.test_auth_to_data_flow()
        self.test_gateway_routing()
        self.test_logging_integration()
        self.test_jwt_propagation()
        self.test_role_based_access_flow()
        self.test_concurrent_requests()
        self.test_error_handling()
        
        # Итоговая статистика
        print("\n" + "=" * 60)
        print("ИТОГОВАЯ СТАТИСТИКА")
        print("=" * 60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        
        print(f"Всего тестов: {total}")
        print(f"Пройдено: {passed} ({passed/total*100:.1f}%)")
        print(f"Провалено: {failed} ({failed/total*100:.1f}%)")
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "results": self.results
        }

if __name__ == "__main__":
    tester = IntegrationTests()
    tester.run_all_tests()

