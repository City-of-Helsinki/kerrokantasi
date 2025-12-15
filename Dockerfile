# Dockerfile for Kerrokantasi backend
# Attemps to provide for both local development and server usage

# branch or tag used to pull python-uwsgi-common.
ARG UWSGI_COMMON_REF=main

FROM helsinki.azurecr.io/ubi9/python-312-gdal AS appbase

# Re-define args, otherwise those aren't available after FROM directive.
ARG UWSGI_COMMON_REF

WORKDIR /app

USER root

# Can be used to inquire about running app
# eg. by running `echo $APP_NAME`
ENV APP_NAME kerrokantasi
# This is server out by Django itself, but aided
# by whitenoise by adding cache headers and also delegating
# much of the work to WSGI-server
ENV STATIC_ROOT /srv/static
# For some reason python output buffering buffers much longer
# while in Docker. Maybe the buffer is larger?
ENV PYTHONUNBUFFERED True

# Generate Finnish locale
RUN localedef -i fi_FI -f UTF-8 fi_FI.UTF-8

# Copy requirements files to image for preloading dependencies
# in their own layer
COPY requirements.txt .

RUN dnf update -y \
    && dnf install -y nmap-ncat && \
    dnf clean all && \
    pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Build and copy specific python-uwsgi-common files.
ADD https://github.com/City-of-Helsinki/python-uwsgi-common/archive/${UWSGI_COMMON_REF}.tar.gz /usr/src/
RUN mkdir -p /usr/src/python-uwsgi-common && \
    tar --strip-components=1 -xzf /usr/src/${UWSGI_COMMON_REF}.tar.gz -C /usr/src/python-uwsgi-common && \
    cp /usr/src/python-uwsgi-common/uwsgi-base.ini /app && \
    uwsgi --build-plugin /usr/src/python-uwsgi-common && \
    rm -rf /usr/src/${UWSGI_COMMON_REF}.tar.gz && \
    rm -rf /usr/src/python-uwsgi-common && \
    uwsgi --build-plugin https://github.com/City-of-Helsinki/uwsgi-sentry && \
    mkdir -p /usr/local/lib/uwsgi/plugins && \
    mv sentry_plugin.so /usr/local/lib/uwsgi/plugins

COPY . .

# Statics are kept inside container image for serving using whitenoise
ENV DEBUG=True
RUN mkdir -p /srv/static && python manage.py collectstatic

# Keep media in its own directory outside home, in case home
# directory forms some sort of attack route
# Usually this would be some sort of volume
RUN mkdir -p /srv/media && chown -R default:root /srv/media

RUN chown -R default:root /app

ENTRYPOINT ["/app/deploy/entrypoint.sh"]

# Both production and dev servers listen on port 8000
EXPOSE 8000

# Next, the development & testing extras
FROM appbase AS development

RUN pip install --no-cache-dir -r requirements-dev.txt

USER default

# And the production image
FROM appbase AS production

RUN django-admin compilemessages

ENV DEBUG=False

USER default
