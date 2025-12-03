"""
Нагрузочное тестирование для проверки производительности и устойчивости
"""
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import statistics

GATEWAY_URL = "http://localhost:8000"
AUTH_URL = f"{GATEWAY_URL}/auth"
DATA_URL = f"{GATEWAY_URL}/data"

class LoadTester:
    def __init__(self):
        self.results = []
        
    def make_request(self, url: str, method: str = "GET", headers: dict = None, 
                    data: dict = None, json_data: dict = None) -> Dict:
        """Выполнение одного запроса с измерением времени"""
        start_time = time.time()
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                if json_data:
                    response = requests.post(url, json=json_data, headers=headers, timeout=10)
                else:
                    response = requests.post(url, data=data, headers=headers, timeout=10)
            else:
                response = requests.request(method, url, headers=headers, timeout=10)
            
            elapsed = time.time() - start_time
            
            return {
                "status_code": response.status_code,
                "elapsed": elapsed,
                "success": 200 <= response.status_code < 300,
                "error": None
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "status_code": 0,
                "elapsed": elapsed,
                "success": False,
                "error": str(e)
            }
    
    def test_rate_limiting_under_load(self, requests_count: int = 20, workers: int = 5):
        """Тест rate limiting под нагрузкой"""
        print(f"\n=== Rate Limiting под нагрузкой ({requests_count} запросов, {workers} потоков) ===")
        
        def make_health_request():
            return self.make_request(f"{GATEWAY_URL}/health")
        
        results = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(make_health_request) for _ in range(requests_count)]
            results = [f.result() for f in as_completed(futures)]
        
        success_count = sum(1 for r in results if r["success"])
        rate_limited = sum(1 for r in results if r["status_code"] == 429)
        avg_time = statistics.mean([r["elapsed"] for r in results])
        max_time = max([r["elapsed"] for r in results])
        
        print(f"Успешных запросов: {success_count}/{requests_count}")
        print(f"Заблокировано (429): {rate_limited}")
        print(f"Среднее время ответа: {avg_time:.3f}s")
        print(f"Максимальное время: {max_time:.3f}s")
        
        return {
            "success_count": success_count,
            "rate_limited": rate_limited,
            "avg_time": avg_time,
            "max_time": max_time
        }
    
    def test_auth_service_load(self, requests_count: int = 50):
        """Тест нагрузки на Auth Service"""
        print(f"\n=== Нагрузка на Auth Service ({requests_count} запросов) ===")
        
        def make_token_request():
            return self.make_request(
                f"{AUTH_URL}/token",
                method="POST",
                data={"username": "admin", "password": "admin123"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        
        results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_token_request) for _ in range(requests_count)]
            results = [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        success_count = sum(1 for r in results if r["success"])
        avg_time = statistics.mean([r["elapsed"] for r in results]) if results else 0
        rps = requests_count / total_time
        
        print(f"Успешных запросов: {success_count}/{requests_count}")
        print(f"Общее время: {total_time:.2f}s")
        print(f"Запросов в секунду: {rps:.2f}")
        print(f"Среднее время ответа: {avg_time:.3f}s")
        
        return {
            "success_count": success_count,
            "rps": rps,
            "avg_time": avg_time,
            "total_time": total_time
        }
    
    def test_data_service_load(self, requests_count: int = 100):
        """Тест нагрузки на Data Service"""
        print(f"\n=== Нагрузка на Data Service ({requests_count} запросов) ===")
        
        # Получаем токен
        token_response = requests.post(
            f"{AUTH_URL}/token",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if token_response.status_code != 200:
            print("Не удалось получить токен")
            return None
        
        token = token_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        def make_data_request():
            return self.make_request(f"{DATA_URL}/data", headers=headers)
        
        results = []
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_data_request) for _ in range(requests_count)]
            results = [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        success_count = sum(1 for r in results if r["success"])
        avg_time = statistics.mean([r["elapsed"] for r in results]) if results else 0
        rps = requests_count / total_time
        
        print(f"Успешных запросов: {success_count}/{requests_count}")
        print(f"Общее время: {total_time:.2f}s")
        print(f"Запросов в секунду: {rps:.2f}")
        print(f"Среднее время ответа: {avg_time:.3f}s")
        
        # Проверяем время ответа по перцентилям
        response_times = sorted([r["elapsed"] for r in results])
        if response_times:
            p50 = response_times[int(len(response_times) * 0.5)]
            p95 = response_times[int(len(response_times) * 0.95)]
            p99 = response_times[int(len(response_times) * 0.99)]
            
            print(f"50-й перцентиль: {p50:.3f}s")
            print(f"95-й перцентиль: {p95:.3f}s")
            print(f"99-й перцентиль: {p99:.3f}s")
        
        return {
            "success_count": success_count,
            "rps": rps,
            "avg_time": avg_time,
            "p50": p50 if response_times else 0,
            "p95": p95 if response_times else 0,
            "p99": p99 if response_times else 0
        }
    
    def test_gateway_routing_performance(self, requests_count: int = 200):
        """Тест производительности маршрутизации Gateway"""
        print(f"\n=== Производительность Gateway Routing ({requests_count} запросов) ===")
        
        results = []
        start_time = time.time()
        
        def make_gateway_request():
            return self.make_request(f"{GATEWAY_URL}/health")
        
        with ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(make_gateway_request) for _ in range(requests_count)]
            results = [f.result() for f in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        success_count = sum(1 for r in results if r["success"])
        avg_time = statistics.mean([r["elapsed"] for r in results]) if results else 0
        rps = requests_count / total_time
        
        print(f"Успешных запросов: {success_count}/{requests_count}")
        print(f"Общее время: {total_time:.2f}s")
        print(f"Запросов в секунду: {rps:.2f}")
        print(f"Среднее время ответа: {avg_time:.3f}s")
        
        return {
            "success_count": success_count,
            "rps": rps,
            "avg_time": avg_time
        }
    
    def test_sustained_load(self, duration_seconds: int = 30, rps: int = 10):
        """Тест устойчивой нагрузки в течение времени"""
        print(f"\n=== Устойчивая нагрузка ({duration_seconds}s при {rps} req/s) ===")
        
        token_response = requests.post(
            f"{AUTH_URL}/token",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if token_response.status_code != 200:
            print("Не удалось получить токен")
            return None
        
        token = token_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        results = []
        start_time = time.time()
        request_count = 0
        
        interval = 1.0 / rps  # Интервал между запросами
        
        while time.time() - start_time < duration_seconds:
            req_start = time.time()
            result = self.make_request(f"{GATEWAY_URL}/health")
            results.append(result)
            request_count += 1
            
            elapsed = time.time() - req_start
            sleep_time = max(0, interval - elapsed)
            time.sleep(sleep_time)
        
        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r["success"])
        avg_time = statistics.mean([r["elapsed"] for r in results]) if results else 0
        actual_rps = request_count / total_time
        
        print(f"Всего запросов: {request_count}")
        print(f"Успешных: {success_count}")
        print(f"Общее время: {total_time:.2f}s")
        print(f"Фактический RPS: {actual_rps:.2f}")
        print(f"Среднее время ответа: {avg_time:.3f}s")
        
        return {
            "total_requests": request_count,
            "success_count": success_count,
            "actual_rps": actual_rps,
            "avg_time": avg_time
        }
    
    def run_all_tests(self):
        """Запуск всех нагрузочных тестов"""
        print("=" * 60)
        print("НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ")
        print("=" * 60)
        
        self.test_rate_limiting_under_load(20, 5)
        self.test_auth_service_load(50)
        self.test_data_service_load(100)
        self.test_gateway_routing_performance(200)
        self.test_sustained_load(30, 10)
        
        print("\n" + "=" * 60)
        print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
        print("=" * 60)

if __name__ == "__main__":
    tester = LoadTester()
    tester.run_all_tests()

