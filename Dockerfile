# Dockerfile for Kerrokantasi backend
# Attempts to provide for both local development and server usage

# branch or tag used to pull python-uwsgi-common.
ARG UWSGI_COMMON_REF=main

FROM helsinki.azurecr.io/ubi9/python-312-gdal AS appbase

# Re-define args, otherwise those aren't available after FROM directive.
ARG UWSGI_COMMON_REF

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.11.32@sha256:df4cae8f3a96d175e2e5f992e597550000edbe78fdc2594d5cd8de1a217f504c /uv /uvx /usr/local/bin/

WORKDIR /app

USER root

# Can be used to inquire about running app
# eg. by running `echo $APP_NAME`
ENV APP_NAME=kerrokantasi \
    STATIC_ROOT=/srv/static \
    PYTHONUNBUFFERED=True \
    UV_PROJECT_ENVIRONMENT=/opt/app-root \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    UV_PYTHON_DOWNLOADS=never

# Generate Finnish locale and install nmap-ncat for health checks
RUN localedef -i fi_FI -f UTF-8 fi_FI.UTF-8 \
    && dnf update -y \
    && dnf install -y nmap-ncat \
    && dnf clean all

# Copy dependency files to image for preloading dependencies
# in their own layer
COPY pyproject.toml uv.lock ./

# Install production dependencies (including prod group for uwsgi/uwsgitop)
RUN uv sync --locked --no-dev --group prod

# Build and copy specific python-uwsgi-common files.
ADD https://github.com/City-of-Helsinki/python-uwsgi-common/archive/${UWSGI_COMMON_REF}.tar.gz /usr/src/
RUN mkdir -p /usr/src/python-uwsgi-common && \
    tar --strip-components=1 -xzf "/usr/src/${UWSGI_COMMON_REF}.tar.gz" -C /usr/src/python-uwsgi-common && \
    cp /usr/src/python-uwsgi-common/uwsgi-base.ini /app && \
    uwsgi --build-plugin /usr/src/python-uwsgi-common && \
    rm -rf "/usr/src/${UWSGI_COMMON_REF}.tar.gz" && \
    rm -rf /usr/src/python-uwsgi-common && \
    uwsgi --build-plugin https://github.com/City-of-Helsinki/uwsgi-sentry && \
    mkdir -p /usr/local/lib/uwsgi/plugins && \
    mv sentry_plugin.so /usr/local/lib/uwsgi/plugins

COPY . .

# Statics are kept inside container image for serving using whitenoise
ENV DEBUG=True
RUN mkdir -p /srv/static && python manage.py collectstatic && \
    mkdir -p /srv/media && chown -R default:root /srv/media && \
    chown -R default:root /app

ENTRYPOINT ["/app/deploy/entrypoint.sh"]

# Both production and dev servers listen on port 8000
EXPOSE 8000

# Next, the development & testing extras
FROM appbase AS development

RUN uv sync --locked --group prod

USER default

# And the production image
FROM appbase AS production

RUN django-admin compilemessages

ENV DEBUG=False

USER default
