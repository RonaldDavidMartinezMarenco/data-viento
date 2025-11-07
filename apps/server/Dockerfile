FROM ghcr.io/astral-sh/uv:python3.13-alpine

WORKDIR /app

RUN apk add --no-cache --virtual .build-deps \
    build-base \
    python3-dev

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project
COPY src/ /app/src

ENTRYPOINT ["uv", "run"]
CMD ["src/main.py"]