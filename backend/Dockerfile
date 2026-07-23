FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY backend/pyproject.toml ./
RUN uv sync --no-dev
COPY backend/app ./app

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
