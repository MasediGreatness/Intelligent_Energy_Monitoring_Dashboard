# syntax=docker/dockerfile:1.7

ARG PYTHON_IMAGE=python:3.12-slim-bookworm

FROM ${PYTHON_IMAGE} AS builder

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /build
COPY requirements-backend.txt ./requirements-backend.txt
RUN python -m venv "${VIRTUAL_ENV}" \
    && pip install --no-cache-dir -r requirements-backend.txt

FROM ${PYTHON_IMAGE} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /workspace

RUN groupadd --gid 10001 energy \
    && useradd --uid 10001 --gid energy --no-create-home --home-dir /nonexistent \
       --shell /usr/sbin/nologin energy

COPY --from=builder /opt/venv /opt/venv
COPY --chown=10001:10001 apps/api/app /workspace/apps/api/app
COPY --chown=10001:10001 apps/api/alembic /workspace/apps/api/alembic
COPY --chown=10001:10001 apps/api/alembic.ini /workspace/apps/api/alembic.ini
WORKDIR /workspace/apps/api

USER 10001:10001
EXPOSE 8000
STOPSIGNAL SIGTERM
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
