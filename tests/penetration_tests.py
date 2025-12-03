"""
Тесты на проникновение для поиска уязвимостей
Симулирует реальные атаки на систему
"""
import requests
import time
import json
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

GATEWAY_URL = "http://localhost:8000"
AUTH_URL = f"{GATEWAY_URL}/auth"
DATA_URL = f"{GATEWAY_URL}/data"

class PenetrationTester:
    def __init__(self):
        self.vulnerabilities = []
        self.warnings = []
        
    def log_vulnerability(self, severity: str, name: str, description: str, details: str = ""):
        """Логирование найденной уязвимости"""
        vuln = {
            "severity": severity,
            "name": name,
            "description": description,
            "details": details
        }
        self.vulnerabilities.append(vuln)
        print(f"\n[!] {severity}: {name}")
        print(f"    {description}")
        if details:
            print(f"    Детали: {details}")
    
    def log_warning(self, name: str, description: str):
        """Логирование предупреждения"""
        warning = {
            "name": name,
            "description": description
        }
        self.warnings.append(warning)
        print(f"[*] WARNING: {name} - {description}")
    
    def test_sql_injection(self):
        """Тест на SQL Injection"""
        print("\n=== SQL Injection Tests ===")
        
        payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT NULL--",
            "admin'--",
            "admin'/*",
            "' OR 1=1--",
            "' OR 'a'='a",
            "') OR ('1'='1",
        ]
        
        vulnerable = False
        for payload in payloads:
            # Тест в username
            response = requests.post(
                f"{AUTH_URL}/token",
                data={"username": payload, "password": "test"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=5
            )
            
            # Проверяем на признаки успешной инъекции
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "access_token" in data:
                        self.log_vulnerability(
                            "CRITICAL",
                            "SQL Injection в аутентификации",
                            f"Payload '{payload}' позволил получить токен",
                            f"Response: {data}"
                        )
                        vulnerable = True
                except:
                    pass
            
            time.sleep(0.1)
        
        if not vulnerable:
            print("[✓] SQL Injection защита работает")
    
    def test_xss_attacks(self):
        """Тест на XSS атаки"""
        print("\n=== XSS Attacks Tests ===")
        
        payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')>",
        ]
        
        vulnerable_count = 0
        for payload in payloads:
            # Тест в URL параметрах
            response = requests.get(
                f"{GATEWAY_URL}/auth/register?test={payload}",
                timeout=5
            )
            
            # Проверяем, отражается ли payload в ответе
            if payload in response.text:
                vulnerable_count += 1
                self.log_vulnerability(
                    "HIGH",
                    "Reflected XSS",
                    f"Payload '{payload}' отражается в ответе",
                    f"Status: {response.status_code}"
                )
        
        if vulnerable_count == 0:
            print("[✓] XSS защита работает")
    
    def test_path_traversal(self):
        """Тест на Path Traversal"""
        print("\n=== Path Traversal Tests ===")
        
        payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
        ]
        
        vulnerable = False
        for payload in payloads:
            response = requests.get(
                f"{DATA_URL}/data/{payload}",
                timeout=5
            )
            
            # Проверяем на признаки чтения файла
            if "root:" in response.text or "[boot loader]" in response.text:
                self.log_vulnerability(
                    "CRITICAL",
                    "Path Traversal",
                    f"Удалось прочитать файл через payload '{payload}'",
                    f"Status: {response.status_code}"
                )
                vulnerable = True
        
        if not vulnerable:
            print("[✓] Path Traversal защита работает")
    
    def test_jwt_manipulation(self):
        """Тест на манипуляцию JWT токенами"""
        print("\n=== JWT Manipulation Tests ===")
        
        # Получаем валидный токен
        response = requests.post(
            f"{AUTH_URL}/token",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            print("[!] Не удалось получить токен для тестирования")
            return
        
        token = response.json().get("access_token")
        
        # Разбираем токен
        parts = token.split('.')
        if len(parts) != 3:
            print("[!] Неверный формат токена")
            return
        
        header, payload, signature = parts
        
        # Тест 1: Изменение алгоритма на None
        import base64
        try:
            # Декодируем payload
            payload_decoded = base64.urlsafe_b64decode(payload + '==')
            payload_dict = json.loads(payload_decoded)
            
            # Меняем роль на admin
            payload_dict['role'] = 'admin'
            payload_modified = base64.urlsafe_b64encode(
                json.dumps(payload_dict).encode()
            ).decode().rstrip('=')
            
            # Создаём токен без подписи (None алгоритм)
            modified_token = f"{header}.{payload_modified}."
            
            test_response = requests.get(
                f"{DATA_URL}/data",
                headers={"Authorization": f"Bearer {modified_token}"},
                timeout=5
            )
            
            if test_response.status_code == 200:
                self.log_vulnerability(
                    "HIGH",
                    "JWT Algorithm Confusion",
                    "Удалось использовать токен с алгоритмом None",
                    f"Status: {test_response.status_code}"
                )
            else:
                print("[✓] JWT алгоритм None отклоняется")
        except Exception as e:
            print(f"[*] JWT манипуляция: {str(e)}")
    
    def test_idor(self):
        """Тест на IDOR (Insecure Direct Object Reference)"""
        print("\n=== IDOR Tests ===")
        
        # Получаем токен обычного пользователя
        user_response = requests.post(
            f"{AUTH_URL}/token",
            data={"username": "user", "password": "user123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if user_response.status_code != 200:
            print("[!] Не удалось получить токен пользователя")
            return
        
        user_token = user_response.json().get("access_token")
        
        # Создаём элемент данных
        create_response = requests.post(
            f"{DATA_URL}/data",
            json={"title": "Private Item", "content": "Secret content"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        if create_response.status_code == 201:
            item_id = create_response.json().get("id")
            
            # Пытаемся получить доступ к элементу другого пользователя
            # (имитируем доступ к элементу с другим ID)
            for test_id in [1, 2, item_id - 1, item_id + 1]:
                if test_id <= 0:
                    continue
                
                test_response = requests.get(
                    f"{DATA_URL}/data/{test_id}",
                    headers={"Authorization": f"Bearer {user_token}"},
                    timeout=5
                )
                
                if test_response.status_code == 200:
                    item_data = test_response.json()
                    # Проверяем, что это не наш элемент
                    if item_data.get("owner_id") != "user":
                        self.log_vulnerability(
                            "HIGH",
                            "IDOR уязвимость",
                            f"Удалось получить доступ к элементу {test_id} другого пользователя",
                            f"Owner: {item_data.get('owner_id')}"
                        )
                        break
            
            print("[✓] IDOR защита проверена")
    
    def test_brute_force(self):
        """Тест на защиту от Brute Force"""
        print("\n=== Brute Force Protection Tests ===")
        
        common_passwords = [
            "password", "123456", "admin", "root", "test",
            "qwerty", "12345", "password123", "admin123"
        ]
        
        blocked = False
        for password in common_passwords:
            response = requests.post(
                f"{AUTH_URL}/token",
                data={"username": "admin", "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=5
            )
            
            if response.status_code == 429:
                blocked = True
                print(f"[✓] Brute Force защита активна после нескольких попыток")
                break
            
            time.sleep(0.1)
        
        if not blocked:
            self.log_warning(
                "Отсутствие защиты от Brute Force",
                "Система не блокирует множественные неудачные попытки входа"
            )
    
    def test_csrf(self):
        """Тест на CSRF защиту"""
        print("\n=== CSRF Tests ===")
        
        # Проверяем наличие CSRF токенов в формах
        response = requests.get(f"{GATEWAY_URL}/docs")
        
        if "csrf" not in response.text.lower() and "x-csrf" not in response.headers:
            self.log_warning(
                "Возможная CSRF уязвимость",
                "Не обнаружены CSRF токены в ответах"
            )
        else:
            print("[✓] CSRF защита присутствует")
    
    def test_information_disclosure(self):
        """Тест на утечку информации"""
        print("\n=== Information Disclosure Tests ===")
        
        # Проверяем ошибки на утечку информации
        response = requests.post(
            f"{AUTH_URL}/token",
            data={"username": "nonexistent", "password": "wrong"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        error_text = response.text.lower()
        sensitive_info = ["database", "sql", "exception", "traceback", "stack trace"]
        
        for info in sensitive_info:
            if info in error_text:
                self.log_vulnerability(
                    "MEDIUM",
                    "Information Disclosure",
                    f"Ответ содержит чувствительную информацию: '{info}'",
                    f"Status: {response.status_code}"
                )
                return
        
        print("[✓] Информация не утекает в ошибках")
    
    def test_dos_protection(self):
        """Тест на защиту от DoS"""
        print("\n=== DoS Protection Tests ===")
        
        # Отправляем множество запросов одновременно
        def make_request():
            try:
                response = requests.get(f"{GATEWAY_URL}/health", timeout=2)
                return response.status_code
            except:
                return 0
        
        print("Отправка 50 параллельных запросов...")
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [f.result() for f in as_completed(futures)]
        
        success_count = sum(1 for r in results if r == 200)
        
        if success_count < 30:
            self.log_vulnerability(
                "MEDIUM",
                "DoS уязвимость",
                f"Система обработала только {success_count}/50 запросов",
                "Возможна проблема с обработкой нагрузки"
            )
        else:
            print(f"[✓] Система устойчива к нагрузке ({success_count}/50 запросов обработано)")
    
    def run_all_tests(self):
        """Запуск всех тестов на проникновение"""
        print("=" * 60)
        print("ТЕСТЫ НА ПРОНИКНОВЕНИЕ")
        print("=" * 60)
        
        self.test_sql_injection()
        self.test_xss_attacks()
        self.test_path_traversal()
        self.test_jwt_manipulation()
        self.test_idor()
        self.test_brute_force()
        self.test_csrf()
        self.test_information_disclosure()
        self.test_dos_protection()
        
        # Итоговый отчёт
        print("\n" + "=" * 60)
        print("ИТОГОВЫЙ ОТЧЁТ")
        print("=" * 60)
        
        critical = sum(1 for v in self.vulnerabilities if v["severity"] == "CRITICAL")
        high = sum(1 for v in self.vulnerabilities if v["severity"] == "HIGH")
        medium = sum(1 for v in self.vulnerabilities if v["severity"] == "MEDIUM")
        
        print(f"\nНайдено уязвимостей:")
        print(f"  CRITICAL: {critical}")
        print(f"  HIGH: {high}")
        print(f"  MEDIUM: {medium}")
        print(f"  Предупреждений: {len(self.warnings)}")
        
        if len(self.vulnerabilities) == 0 and len(self.warnings) == 0:
            print("\n[✓] Критические уязвимости не обнаружены")
        
        return {
            "vulnerabilities": self.vulnerabilities,
            "warnings": self.warnings
        }

if __name__ == "__main__":
    tester = PenetrationTester()
    tester.run_all_tests()

