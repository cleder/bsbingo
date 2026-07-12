# syntax=docker/dockerfile:1
#
# Build context is the REPO ROOT, not backend/ (see .github/workflows/main.yaml
# build-backend-image job: context: ., file: ./backend/Dockerfile) -- dependencies
# are managed by the root-level pyproject.toml/uv.lock via uv, not a package-local
# requirements file.

FROM python:3.14-slim AS build

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

RUN pip install --no-cache-dir --upgrade uv

WORKDIR /src

# psycopg[binary,pool] bundles libpq, so no libpq-dev/libpq5 system packages are
# needed to build or run this image.
COPY pyproject.toml uv.lock ./

ARG TEST=no

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project $(if [ "$TEST" = "yes" ]; then echo --group test; fi)

# Application image
FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/bin:${PATH}" \
    HOME=/tmp

WORKDIR /app/src

RUN adduser --system --no-create-home django

COPY --chown=django:django --from=build /app /app
COPY --chown=django:django backend/ /app/src/

USER django

EXPOSE 8000

# k8s always overrides this command explicitly (see k8s/base/django.yaml and the
# gunicorn/uvicorn override in k8s/sandbox/kustomization.yaml); this default only
# supports `docker run`/local testing of the image in isolation.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
