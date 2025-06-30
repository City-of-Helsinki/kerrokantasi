# Dockerfile for Kerrokantasi backend
# Attemps to provide for both local development and server usage

FROM helsinki.azurecr.io/ubi9/python-39-gdal AS appbase

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

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir uwsgi && \
    uwsgi --build-plugin https://github.com/City-of-Helsinki/python-uwsgi-common

ADD https://raw.githubusercontent.com/City-of-Helsinki/python-uwsgi-common/main/uwsgi-base.ini /app/

# Sentry CLI for sending events from non-Python processes to Sentry
# eg. https://docs.sentry.io/cli/send-event/#bash-hook
RUN curl -sL https://sentry.io/get-cli/ | bash

# Copy requirements files to image for preloading dependencies
# in their own layer
COPY requirements.txt ./

# deploy/requirements.txt must reference the base requirements
RUN pip install --require-hashes --no-cache-dir -r requirements.txt

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

RUN pip install --require-hashes --no-cache-dir -r requirements-dev.txt

USER default

# And the production image
FROM appbase AS production

RUN django-admin compilemessages

ENV DEBUG=False

USER default
