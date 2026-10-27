FROM python:3.11-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /usr/local/bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" AIDEMO_HOST=0.0.0.0 AIDEMO_CACHE_DIR=/cache \
    GRADIO_ANALYTICS_ENABLED=False HF_HUB_DISABLE_TELEMETRY=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 libgomp1 ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 aidemo \
    && mkdir /cache && chown aidemo:aidemo /cache
COPY pyproject.toml uv.lock README.md LICENSE CHANGELOG.md ./
COPY src ./src
COPY configs ./configs
ARG DEMO_EXTRA=detection
RUN uv sync --frozen --no-dev --extra "$DEMO_EXTRA" --no-editable
USER aidemo
EXPOSE 7860
CMD ["aidemo", "run", "detection", "--config", "configs/detection.yaml"]
