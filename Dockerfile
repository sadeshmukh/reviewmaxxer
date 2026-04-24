FROM ghcr.io/astral-sh/uv:alpine

WORKDIR /bot
COPY . .
RUN uv sync --frozen-lockfile
CMD ["uv", "run", "main.py"]