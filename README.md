# Payment Processing Service

Асинхронный микросервис обработки платежей на FastAPI, SQLAlchemy 2.0, PostgreSQL, RabbitMQ и FastStream.

## Запуск

```bash
docker compose up --build
```

API: http://localhost:8000/docs

## Примеры

Создание платежа:

```bash
curl -X POST http://localhost:8000/api/v1/payments \
  -H "X-API-Key: test-api-key" \
  -H "Idempotency-Key: order-123" \
  -H "Content-Type: application/json" \
  -d '{"amount":"100.00","currency":"RUB","description":"Test payment","metadata":{"order_id":"123"},"webhook_url":"https://example.com/webhook"}'
```

Получение платежа:

```bash
curl http://localhost:8000/api/v1/payments/PAYMENT_ID \
  -H "X-API-Key: test-api-key"
```

## Архитектура

1. API создаёт платёж и outbox-событие в одной транзакции.
2. Outbox Relay читает события и публикует их в очередь `payments.new`.
3. Consumer эмулирует обработку 2-5 секунд, обновляет статус и отправляет webhook.
4. Consumer выполняет до 3 попыток с задержками 1 и 2 секунды.
5. Окончательно необработанные сообщения попадают в `payments.new.dlq`.

## Переменные окружения

См. `.env.example`.

## Тесты

Автотесты не включены, так как не требовались техническим заданием.
