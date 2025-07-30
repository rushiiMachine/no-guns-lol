FROM python:3.13-alpine
WORKDIR /app

# Install dependencies
RUN --mount=from=ghcr.io/astral-sh/uv,source=/uv,target=/bin/uv \
    --mount=source=./pyproject.toml,target=/app/pyproject.toml \
    --mount=source=./uv.lock,target=/app/uv.lock \
    apk add --no-cache git \
    && uv sync --locked --no-cache \
    && apk --purge del git

ADD main.py .
ADD no_guns_lol ./no_guns_lol
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT [ "python3", "main.py" ]
