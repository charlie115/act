##############
# BASE IMAGE #
##############
FROM python:3.10 as base

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt update
RUN apt install -y nodejs npm
RUN npm install pm2 -g

WORKDIR /opt/community_drf/

COPY ./requirements/base.txt requirements/base.txt
COPY ./manage.py manage.py
COPY ./config config/
COPY ./lib lib/
COPY ./templates templates/
COPY ./apps apps/

RUN pip install --no-cache-dir -r requirements/base.txt

RUN mkdir -p /opt/community_drf/media
RUN mkdir -p /opt/community_drf/static


#############
# DEV IMAGE #
#############
FROM base as dev

COPY ./.env.dev .env
COPY ./requirements/dev.txt requirements/dev.txt
COPY ./docker/start-dev-server.sh /usr/local/bin/start-dev-server.sh

RUN chmod +x /usr/local/bin/start-dev-server.sh
RUN pip install --no-cache-dir -r requirements/dev.txt

CMD ["start-dev-server.sh"]


##############
# TEST IMAGE #
##############
FROM dev as test

# Same as dev, just use corresponding env file for testing
COPY ./.env.test .env

CMD ["start-dev-server.sh"]


####################
# PRODUCTION IMAGE #
####################
FROM base as prod

COPY ./.env.prod .env
COPY ./requirements/prod.txt requirements/prod.txt
COPY ./docker/start-prod-server.sh /usr/local/bin/start-prod-server.sh

RUN chmod +x /usr/local/bin/start-prod-server.sh
RUN pip install --no-cache-dir -r requirements/prod.txt

CMD ["start-prod-server.sh"]
