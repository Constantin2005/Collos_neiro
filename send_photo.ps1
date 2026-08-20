param([string]$ImagePath)

if (-not $ImagePath) {
    Write-Host "Укажите путь к фото: .\send_photo.ps1 D:\photo.jpg"
    exit
}

if (-not (Test-Path $ImagePath)) {
    Write-Host "Файл не найден: $ImagePath"
    exit
}

try {
    $base64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($ImagePath))
} catch {
    Write-Host "Ошибка чтения файла: $_"
    exit
}

$body = @{
    type = "image"
    image_base64 = $base64
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/analyze" -Method Post -Body $body -ContentType "application/json"
    $request_id = $response.request_id
    Write-Host " Задание отправлено. Request ID: $request_id"
} catch {
    Write-Host " Ошибка отправки запроса: $_"
    exit
}

Write-Host "⏳ Ожидание результата..."
$done = $false
while (-not $done) {
    Start-Sleep -Seconds 2
    try {
        $result = Invoke-RestMethod -Uri "http://localhost:8000/result/$request_id" -Method Get
        Write-Host "Результат: $($result.result)"
        $done = $true
    } catch {
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode -eq 404) {
            Write-Host "⏳ Ещё обрабатывается..."
        } else {
            Write-Host " Ошибка получения результата: $_"
            $done = $true
        }
    }
}