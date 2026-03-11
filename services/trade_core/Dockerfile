# Start from the Python 3.11 image
FROM python:3.11 AS base

# Install system dependencies for building Python packages with C extensions
RUN apt-get update

# Install Redis
RUN apt-get install -y redis-server

# Install Apache HTTP server utilities for rotating logs
RUN apt-get install apache2-utils

# # Start Redis server --> This will be handled by start-env-service.sh
# CMD redis-server

# Set WORKDIR
WORKDIR /home/trade_core/

# Copy the trade_core
COPY services/trade_core/trade_core trade_core/

# Copy the requirements.txt
COPY services/trade_core/requirements.txt requirements.txt

# Copy shared python package
COPY packages/python/acw_common /opt/acw_common

ENV PYTHONPATH=/home/trade_core/trade_core:/opt/acw_common

# Update pip
RUN pip install --upgrade pip

# Install requirements.txt
RUN pip install -r requirements.txt

# Set WORKDIR for executing start-env-service.sh
WORKDIR /home/trade_core/trade_core/

#############
# DEV IMAGE #
#############
# For trade_core
FROM base AS dev
COPY services/trade_core/trade_core/docker/start-dev-service.sh /usr/local/bin/start-dev-service.sh
COPY services/trade_core/.env.dev .env
CMD ["start-dev-service.sh"]

# For trade_core_api
FROM base AS api_dev
COPY services/trade_core/trade_core/docker/start-api-dev-service.sh /usr/local/bin/start-api-dev-service.sh
COPY services/trade_core/.env.dev .env
CMD ["start-api-dev-service.sh"]

#############
# TEST IMAGE #
#############
# For trade_core
FROM base AS test
COPY services/trade_core/trade_core/docker/start-test-service.sh /usr/local/bin/start-test-service.sh
COPY services/trade_core/.env.test .env
CMD ["start-test-service.sh"]

# For trade_core_api
FROM base AS api_test
COPY services/trade_core/trade_core/docker/start-api-test-service.sh /usr/local/bin/start-api-test-service.sh
COPY services/trade_core/.env.test .env
CMD ["start-api-test-service.sh"]

##############
# PROD IMAGE #
##############
# For trade_core
FROM base AS prod
COPY services/trade_core/trade_core/docker/start-prod-service.sh /usr/local/bin/start-prod-service.sh
COPY services/trade_core/.env.prod .env
CMD ["start-prod-service.sh"]

# For trade_core_api
FROM base AS api_prod
COPY services/trade_core/trade_core/docker/start-api-prod-service.sh /usr/local/bin/start-api-prod-service.sh
COPY services/trade_core/.env.prod .env
CMD ["start-api-prod-service.sh"]
