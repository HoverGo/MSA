# PowerShell скрипт для генерации сертификатов (Windows)

$certPath = "..\certs"
if (-not (Test-Path $certPath)) {
    New-Item -ItemType Directory -Path $certPath
}

# Генерация самоподписанного сертификата
$cert = New-SelfSignedCertificate `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -DnsName "localhost" `
    -FriendlyName "MSA API Gateway Certificate" `
    -NotAfter (Get-Date).AddYears(1)

# Экспорт сертификата в PFX
$pfxPassword = ConvertTo-SecureString -String "password" -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath "$certPath\server.pfx" -Password $pfxPassword

# Экспорт приватного ключа в PEM
$keyPath = "$certPath\server.key"
$crtPath = "$certPath\server.crt"

# Используем OpenSSL если доступен, иначе предупреждение
Write-Host "Для Windows рекомендуется использовать OpenSSL для генерации сертификатов в формате PEM"
Write-Host "Скачайте OpenSSL или используйте WSL для запуска generate_certs.sh"

# Альтернативный вариант - использовать certutil (базовый функционал)
certutil -exportPFX -p password My "$certPath\server.pfx" $cert.Thumbprint

Write-Host "Сертификат создан: $certPath\server.pfx"
Write-Host "Примечание: Для production используйте подписанные сертификаты от доверенного CA"

