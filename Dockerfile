FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON=/usr/local/bin/python3 \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 \
    PORT=5042 \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app.py ./
COPY requeststoken ./requeststoken
COPY templates ./templates
COPY static ./static

EXPOSE 5042

CMD ["uv", "run", "--frozen", "--no-dev", "--no-sync", "python", "app.py"]
