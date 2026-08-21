# 🚀 ProjectHub — Backend Service

**ProjectHub** — это масштабируемый REST API сервис для управления проектами и версионированием документов. Написан на Python 3.12 с использованием асинхронного стека (FastAPI, SQLAlchemy 2.0, asyncpg) и микросервисной архитектуры под управлением Docker Compose.

---

## 🛠 Технологический стек

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12)
* **Database & ORM:** PostgreSQL, [SQLAlchemy 2.0 (Async)](https://www.sqlalchemy.org/), [Alembic](https://alembic.sqlalchemy.org/) (миграции)
* **Auth & Security:** JWT (Access & Refresh), [Pwdlib](https://pwdlib.readthedocs.io/) (Argon2id)
* **Object Storage:** S3 / [MinIO](https://min.io/) (загрузка файлов и версионирование документов)
* **Cache & Async Tasks:** Redis, [ARQ](https://arq-docs.helpmanual.io/)
* **Monitoring & Health:** Prometheus metrics (`/metrics`), Healthcheck endpoints (`/health/ready`, `/health/live`)
* **Package Manager:** [uv](https://github.com/astral-sh/uv)

---

## 📐 Архитектура и функционал

Проект построен по модульной архитектуре (**Feature-first**):

* **Auth & Users (`app/users`, `app/auth`):** Регистрация, аутентификация, хеширование паролей Argon2id, JWT авторизация.
* **Projects & RBAC (`app/projects`):** Создание проектов, управление участниками и разграничение ролей (`owner`, `member`).
* **Documents (`app/documents`):** Загрузка файлов в MinIO/S3, генерация уникальных ключей, отслеживание версий файлов.
* **Shared (`app/shared`):** Общие сессии БД, настройки Pydantic Settings, логгер, клиенты S3 и Redis.

---

## 🚀 Быстрый запуск

### Вариант 1. Через Docker Compose (Рекомендуется)

Запуск всей инфраструктуры (FastAPI app, ARQ Worker, PostgreSQL, Redis, MinIO) одной командой:

```bash
docker-compose up --build -d
