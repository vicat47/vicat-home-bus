FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY homebus/ ./homebus/
COPY cli/ ./cli/

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "homebus.api:app", "--host", "0.0.0.0", "--port", "8080"]
