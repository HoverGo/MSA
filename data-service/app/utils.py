"""Утилиты для работы с Auth Service"""
import httpx
import os

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")

async def verify_jwt_token_from_auth_service(token: str) -> dict:
    """Проверка JWT токена через Auth Service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/verify-token",
                json={"token": token},
                timeout=5.0
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("valid"):
                raise Exception("Invalid token")
            
            payload = data.get("payload", {})
            return {
                "username": payload.get("sub"),
                "role": payload.get("role"),
                "user_id": payload.get("sub")  # Используем username как user_id для упрощения
            }
        except httpx.RequestError as e:
            raise Exception(f"Auth service unavailable: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Auth service error: {str(e)}")

