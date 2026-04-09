# URL Shortener

Микросервис для сокращения ссылок с event-driven архитектурой.

## Стек

- **FastAPI** — API
- **PostgreSQL** — хранилище ссылок
- **Redis** — кэш для быстрого resolve
- **RabbitMQ** — очередь событий кликов
- **Docker Compose** — оркестрация

## Архитектура

```
Client → FastAPI (app) → Redis (кэш) → PostgreSQL (хранилище)
                ↓
           RabbitMQ (очередь кликов)
                ↓
           Worker (обновляет счётчик в PostgreSQL)
```

При каждом GET-запросе на короткую ссылку API публикует событие в RabbitMQ. Отдельный воркер читает очередь и инкрементит счётчик переходов в БД. Это разделяет ответственность: API отвечает быстро, а запись статистики происходит асинхронно.

## Запуск

### Требования

- Docker и Docker Compose

### Шаги

1. Клонировать репозиторий
```bash
git clone https://github.com/mtntr/url-shortener.git
cd url-shortener
```

2. Создать `.env` из шаблона и при необходимости отредактировать
```bash
cp .env.example .env
```

3. Запустить
```bash
docker compose up -d --build 
```

4. API доступен на `http://localhost:8000` либо можете подставить адрес своего сервера и проверять снаружи.

## API

### Создать короткую ссылку

```bash
curl -X POST http://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/very/long/path"}'
```

Ответ:
```json
{
  "short_id": "kR4mXvT",
  "short_url": "http://localhost:8000/kR4mXvT"
}
```

### Перейти по короткой ссылке

```bash
curl -L http://localhost:8000/kR4mXvT
```

### Получить статистику

```bash
curl http://localhost:8000/stats/kR4mXvT
```

Ответ:
```json
{
  "short_id": "kR4mXvT",
  "original_url": "https://example.com/very/long/path",
  "clicks": 5
}
```

## Тесты

```bash
docker compose exec app pytest tests/ -v
```

## Логи

```bash
docker compose logs app --tail 50
docker compose logs worker --tail 50
docker compose logs app worker -f
```

## Остановка

```bash
docker compose down
```

Для полной очистки (включая данные):
```bash
docker compose down -v
```
