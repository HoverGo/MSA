FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app/app

# Для HTTPS раскомментируйте строку ниже и закомментируйте обычную
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "/app/certs/server.key", "--ssl-certfile", "/app/certs/server.crt"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

