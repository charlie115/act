# Start from the Python 3.11 image
FROM python:3.11 AS base

# Install system dependencies for building Python packages with C extensions
RUN apt-get update

# Install Redis
RUN apt-get install -y redis-server

# Install Apache HTTP server utilities for rotating logs
RUN apt-get install apache2-utils

# Start Redis server --> This will be handled by start-env-service.sh
CMD redis-server

# Set WORKDIR
WORKDIR /home/info_core/

# Copy the info_core
COPY services/info_core/info_core info_core/

# Copy the requirements.txt
COPY services/info_core/requirements.txt requirements.txt

# Copy shared python package
COPY packages/python/acw_common /opt/acw_common

ENV PYTHONPATH=/opt/acw_common

# Update pip
RUN pip install --upgrade pip

# Install requirements.txt
RUN pip install -r requirements.txt

# Set WORKDIR for executing start-env-service.sh
WORKDIR /home/info_core/info_core/

#############
# DEV IMAGE #
#############
FROM base AS dev

COPY services/info_core/info_core/docker/start-dev-service.sh /usr/local/bin/start-dev-service.sh
COPY services/info_core/.env.dev .env

CMD ["start-dev-service.sh"]

#############
# TEST IMAGE #
#############
FROM base AS test

COPY services/info_core/info_core/docker/start-test-service.sh /usr/local/bin/start-test-service.sh
COPY services/info_core/.env.test .env

CMD ["start-test-service.sh"]

##############
# PROD IMAGE #
##############
FROM base AS prod

COPY services/info_core/info_core/docker/start-prod-service.sh /usr/local/bin/start-prod-service.sh
COPY services/info_core/.env.prod .env

CMD ["start-prod-service.sh"]
