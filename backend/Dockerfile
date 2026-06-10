FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./

RUN pip install --upgrade pip && \
    pip install fastapi uvicorn sqlalchemy alembic argon2-cffi python-jose psycopg2-binary \
    pydantic pydantic-settings httpx passlib==1.7.4 bcrypt==4.0.1 testcontainers fastapi-mail apscheduler \
    python-multipart

COPY . .

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]