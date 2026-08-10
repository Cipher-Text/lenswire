FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/app \
    XDG_CACHE_HOME=/app/.cache

WORKDIR /app

RUN addgroup --system lenswire && adduser --system --ingroup lenswire lenswire

COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data /app/.cache \
    && chown -R lenswire:lenswire /app

USER lenswire

HEALTHCHECK --interval=60s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "from app.settings import settings; print(settings.database_path)" || exit 1

CMD ["python", "-m", "app.main"]
