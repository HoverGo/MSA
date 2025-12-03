#!/bin/bash

# Генерация самоподписанных сертификатов для TLS/HTTPS

mkdir -p ../certs

# Генерация приватного ключа
openssl genrsa -out ../certs/server.key 2048

# Генерация самоподписанного сертификата
openssl req -new -x509 -key ../certs/server.key -out ../certs/server.crt -days 365 -subj "/C=RU/ST=Moscow/L=Moscow/O=MSA/CN=localhost"

echo "Сертификаты созданы в директории certs/"
echo "server.key - приватный ключ"
echo "server.crt - сертификат"

