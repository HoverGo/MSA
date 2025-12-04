"""
Сводный отчёт по атакам и защитам.

Для каждой категории атак / механизма защиты считает:
- количество попыток
- сколько было УСПЕШНЫХ атак (т.е. защита НЕ сработала)
- сколько было ЗАБЛОКИРОВАНО (защита сработала)
- среднее время отклика, мс

Отчёт печатается в человекочитаемом виде и в конце как JSON.
"""

import time
import json
from statistics import mean
from typing import Dict, List, Tuple

import requests


GATEWAY_URL = "http://localhost:8000"
AUTH_URL = f"{GATEWAY_URL}/auth"
DATA_URL = f"{GATEWAY_URL}/data"
LOGGING_URL = f"{GATEWAY_URL}/logging"


class AttackStats:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.attempts: int = 0
        self.blocked: int = 0
        self.success: int = 0  # успех атаки = защита не сработала
        self.times_ms: List[float] = []

    def add(self, blocked: bool, elapsed_ms: float):
        self.attempts += 1
        if blocked:
            self.blocked += 1
        else:
            self.success += 1
        self.times_ms.append(elapsed_ms)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "attempts": self.attempts,
            "blocked": self.blocked,
            "successful_attacks": self.success,
            "avg_response_ms": mean(self.times_ms) if self.times_ms else 0.0,
        }


class AttackReportRunner:
    def __init__(self):
        self.stats: Dict[str, AttackStats] = {}
        self._admin_token: str | None = None
        self._user_token: str | None = None

    # ===== Helpers =====

    def _get_or_create_stats(self, key: str, name: str, description: str) -> AttackStats:
        if key not in self.stats:
            self.stats[key] = AttackStats(name=name, description=description)
        return self.stats[key]

    def _timed_request(self, method: str, url: str, **kwargs) -> Tuple[requests.Response, float]:
        start = time.perf_counter()
        resp = requests.request(method, url, timeout=5, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return resp, elapsed_ms

    def get_admin_token(self) -> str | None:
        if self._admin_token:
            return self._admin_token
        try:
            resp, _ = self._timed_request(
                "POST",
                f"{AUTH_URL}/token",
                data={"username": "admin", "password": "admin123"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if resp.status_code == 200:
                self._admin_token = resp.json().get("access_token")
        except Exception:
            return None
        return self._admin_token

    def get_user_token(self) -> str | None:
        if self._user_token:
            return self._user_token
        try:
            resp, _ = self._timed_request(
                "POST",
                f"{AUTH_URL}/token",
                data={"username": "user", "password": "user123"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if resp.status_code == 200:
                self._user_token = resp.json().get("access_token")
        except Exception:
            return None
        return self._user_token

    # ===== Per‑protection attack suites =====

    def run_jwt_attacks(self):
        """
        JWT защита:
        - валидный токен (ожидаем пропуск)
        - явный мусорный токен / истёкший токен (ожидаем блокировку)
        """
        s = self._get_or_create_stats(
            "jwt",
            "JWT защита",
            "Проверка отклонения невалидных / истёкших токенов",
        )

        # Валидный токен (для базовой линии времени)
        token = self.get_admin_token()
        if token:
            resp, t = self._timed_request(
                "GET",
                f"{DATA_URL}/data",
                headers={"Authorization": f"Bearer {token}"},
            )
            # валидный запрос не должен блокироваться
            s.add(blocked=resp.status_code >= 400, elapsed_ms=t)

        # Невалидный токен
        for payload in ["invalid.token.here", "aaa.bbb.ccc"]:
            resp, t = self._timed_request(
                "GET",
                f"{DATA_URL}/data",
                headers={"Authorization": f"Bearer {payload}"},
            )
            # считаем блокировкой всё, что не 2xx
            s.add(blocked=resp.status_code >= 400, elapsed_ms=t)

    def run_waf_attacks(self):
        """
        WAF: XSS и SQLi паттерны в URL/теле.
        """
        s = self._get_or_create_stats(
            "waf",
            "WAF защита",
            "Фильтрация XSS/SQLi в URL, теле и заголовках",
        )

        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
        ]
        for p in xss_payloads:
            resp, t = self._timed_request(
                "GET",
                f"{GATEWAY_URL}/auth/register?test={p}",
            )
            # считаем блокировкой 403 от WAF
            s.add(blocked=resp.status_code == 403, elapsed_ms=t)

        sqli_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "SELECT * FROM users",
        ]
        for p in sqli_payloads:
            resp, t = self._timed_request(
                "POST",
                f"{AUTH_URL}/register",
                json={"username": p, "email": "test@test.com", "password": "test"},
            )
            # блокировка — 4xx/5xx, успех атаки — 2xx
            s.add(blocked=resp.status_code >= 400, elapsed_ms=t)

    def run_rate_limit_attacks(self, total_requests: int = 15):
        """
        Rate limiting: серия быстрых запросов к /health через gateway.
        """
        s = self._get_or_create_stats(
            "rate_limit",
            "Rate limiting",
            "Ограничение частоты запросов через API Gateway",
        )

        for _ in range(total_requests):
            resp, t = self._timed_request("GET", f"{GATEWAY_URL}/health")
            # 429 => заблокировано, всё остальное считаем пропущенным
            s.add(blocked=resp.status_code == 429, elapsed_ms=t)
            time.sleep(0.05)

    def run_rbac_attacks(self):
        """
        RBAC: обычный пользователь пытается удалить данные, админ — может.
        """
        s = self._get_or_create_stats(
            "rbac",
            "RBAC (ролевой доступ)",
            "Ограничение операций по ролям (user vs admin)",
        )

        user_token = self.get_user_token()
        admin_token = self.get_admin_token()
        if not user_token or not admin_token:
            return

        # создаём элемент от пользователя
        create_resp, _ = self._timed_request(
            "POST",
            f"{DATA_URL}/data",
            json={"title": "RBAC Test", "content": "RBAC"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        if create_resp.status_code != 201:
            return
        item_id = create_resp.json().get("id")

        # попытка удалить как обычный пользователь — должна блокироваться
        resp, t = self._timed_request(
            "DELETE",
            f"{DATA_URL}/data/{item_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        s.add(blocked=resp.status_code == 403, elapsed_ms=t)

        # удаление как админ — не блокируется (для метрики времени)
        resp, t = self._timed_request(
            "DELETE",
            f"{DATA_URL}/data/{item_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        s.add(blocked=resp.status_code >= 400, elapsed_ms=t)

    def run_api_key_hmac_attacks(self):
        """
        API ключи + HMAC: правильная и неправильная подписи, устаревший timestamp.
        """
        s = self._get_or_create_stats(
            "api_keys_hmac",
            "API ключи и HMAC",
            "Проверка подписи и временного окна для API ключей",
        )

        token = self.get_admin_token()
        if not token:
            return

        # создаём API key
        resp, _ = self._timed_request(
            "POST",
            f"{AUTH_URL}/api-keys",
            json={"name": "Report Key", "permissions": ["read"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code != 200:
            return

        key_data = resp.json()
        key_id = key_data.get("key_id")
        secret_key = key_data.get("secret_key")

        # 1) корректная подпись — не должна блокироваться
        ts = str(int(time.time()))
        msg = f"{ts}{key_id}"
        sig = requests.utils.hashlib.sha256(secret_key.encode() + msg.encode()).hexdigest()

        resp, t = self._timed_request(
            "POST",
            f"{AUTH_URL}/verify-api-key",
            headers={
                "X-API-Key-ID": key_id,
                "X-API-Signature": sig,
                "X-API-Timestamp": ts,
            },
        )
        s.add(blocked=resp.status_code >= 400, elapsed_ms=t)

        # 2) неправильная подпись — должна блокироваться
        resp, t = self._timed_request(
            "POST",
            f"{AUTH_URL}/verify-api-key",
            headers={
                "X-API-Key-ID": key_id,
                "X-API-Signature": "wrong_signature",
                "X-API-Timestamp": ts,
            },
        )
        s.add(blocked=resp.status_code == 401, elapsed_ms=t)

        # 3) устаревший timestamp — должна блокироваться
        old_ts = str(int(time.time()) - 400)
        old_msg = f"{old_ts}{key_id}"
        old_sig = requests.utils.hashlib.sha256(secret_key.encode() + old_msg.encode()).hexdigest()

        resp, t = self._timed_request(
            "POST",
            f"{AUTH_URL}/verify-api-key",
            headers={
                "X-API-Key-ID": key_id,
                "X-API-Signature": old_sig,
                "X-API-Timestamp": old_ts,
            },
        )
        s.add(blocked=resp.status_code == 401, elapsed_ms=t)

    def run_ztna_attacks(self):
        """
        ZTNA: динамические токены — валидный и невалидный.
        """
        s = self._get_or_create_stats(
            "ztna",
            "ZTNA динамические токены",
            "Проверка валидации динамических токенов",
        )

        token = self.get_admin_token()
        if not token:
            return

        # создаём динамический токен
        resp, _ = self._timed_request(
            "POST",
            f"{AUTH_URL}/dynamic-tokens",
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code != 200:
            return
        dyn_token = resp.json().get("token")

        # валидный
        resp, t = self._timed_request(
            "POST",
            f"{AUTH_URL}/verify-dynamic-token",
            json={"token": dyn_token},
        )
        s.add(blocked=resp.status_code >= 400, elapsed_ms=t)

        # невалидный
        resp, t = self._timed_request(
            "POST",
            f"{AUTH_URL}/verify-dynamic-token",
            json={"token": "invalid_token_12345"},
        )
        s.add(blocked=resp.status_code == 401, elapsed_ms=t)

    def run_idor_attacks(self):
        """
        IDOR: пользователь пытается получить чужие объекты по ID.
        """
        s = self._get_or_create_stats(
            "idor",
            "IDOR",
            "Защита от несанкционированного доступа к объектам по ID",
        )

        user_token = self.get_user_token()
        if not user_token:
            return

        # создаём элемент пользователя
        create_resp, _ = self._timed_request(
            "POST",
            f"{DATA_URL}/data",
            json={"title": "Private Item", "content": "Secret"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        if create_resp.status_code != 201:
            return
        item_id = create_resp.json().get("id")

        # пробуем доступ к соседним ID
        for test_id in [item_id - 1, item_id + 1]:
            if test_id <= 0:
                continue
            resp, t = self._timed_request(
                "GET",
                f"{DATA_URL}/data/{test_id}",
                headers={"Authorization": f"Bearer {user_token}"},
            )
            # успех атаки — получили 200 и owner_id != user
            blocked = True
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if data.get("owner_id") != "user":
                        blocked = False
                except Exception:
                    pass
            s.add(blocked=blocked, elapsed_ms=t)

    def run_dos_attacks(self, parallel_requests: int = 30):
        """
        DoS / нагрузка: множество параллельных запросов на /health.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        s = self._get_or_create_stats(
            "dos",
            "DoS / нагрузка",
            "Устойчивость к высокой параллельной нагрузке",
        )

        def make_request() -> Tuple[int, float]:
            try:
                start = time.perf_counter()
                r = requests.get(f"{GATEWAY_URL}/health", timeout=2)
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                return r.status_code, elapsed_ms
            except Exception:
                return 0, 2000.0

        with ThreadPoolExecutor(max_workers=20) as ex:
            futures = [ex.submit(make_request) for _ in range(parallel_requests)]
            for f in as_completed(futures):
                status, t = f.result()
                # считаем "успехом атаки" случаи, когда система отвечает не 200
                blocked = status == 200
                s.add(blocked=blocked, elapsed_ms=t)

    # ===== Orchestration =====

    def run_all(self) -> Dict[str, Dict]:
        print("=" * 60)
        print("СВОДНЫЙ ОТЧЁТ ПО АТАКАМ И ЗАЩИТАМ")
        print("=" * 60)

        self.run_jwt_attacks()
        self.run_waf_attacks()
        self.run_rate_limit_attacks()
        self.run_rbac_attacks()
        self.run_api_key_hmac_attacks()
        self.run_ztna_attacks()
        self.run_idor_attacks()
        self.run_dos_attacks()

        # Человекочитаемый вывод
        print("\n" + "=" * 60)
        print("РЕЗЮМЕ ПО КАЖДОЙ ЗАЩИТЕ")
        print("=" * 60)
        for key, s in self.stats.items():
            d = s.to_dict()
            print(f"\n[{key}] {d['name']}")
            print(f"  Описание         : {d['description']}")
            print(f"  Попыток атак     : {d['attempts']}")
            print(f"  Успешных атак    : {d['successful_attacks']}")
            print(f"  Заблокировано    : {d['blocked']}")
            print(f"  Средний отклик   : {d['avg_response_ms']:.2f} ms")

        summary = {k: v.to_dict() for k, v in self.stats.items()}

        print("\n" + "=" * 60)
        print("JSON ОТЧЁТ")
        print("=" * 60)
        print(json.dumps(summary, indent=2, ensure_ascii=False))

        return summary


if __name__ == "__main__":
    runner = AttackReportRunner()
    runner.run_all()


