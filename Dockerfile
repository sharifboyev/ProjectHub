FROM python:3.12-slim

# Установка uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Копируем файлы окружения и зависимостей
COPY pyproject.toml uv.lock README.md ./

# Устанавливаем зависимости без самого проекта
RUN uv sync --frozen --no-install-project

# Копируем исходный код
COPY app /app/app
COPY migrations /app/migrations
COPY alembic.ini /app/alembic.ini

ENV PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]