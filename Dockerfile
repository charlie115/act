##############
# BASE IMAGE #
##############
FROM python:3.10 as base

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN addgroup --system django \
    && adduser --system --ingroup django django

WORKDIR /home/django/community_drf/

USER root

COPY --chown=django:django ./requirements/base.txt requirements/base.txt
COPY --chown=django:django ./manage.py manage.py
COPY --chown=django:django ./config config/
COPY --chown=django:django ./lib lib/
COPY --chown=django:django ./apps apps/

RUN pip install --no-cache-dir -r requirements/base.txt

RUN mkdir -p /home/django/community_drf/media

RUN chown django:django /home/django/community_drf/media

USER django


#############
# DEV IMAGE #
#############
FROM base as dev

USER root

COPY --chown=django:django ./.env.dev .env
COPY --chown=django:django ./requirements/dev.txt requirements/dev.txt
COPY --chown=django:django ./docker/start-dev-server.sh /usr/local/bin/start-dev-server.sh

RUN chmod +x /usr/local/bin/start-dev-server.sh
RUN pip install --no-cache-dir -r requirements/dev.txt

USER django

CMD ["start-dev-server.sh"]


##############
# TEST IMAGE #
##############
FROM dev as test

# Same as dev, just use corresponding env file for testing
COPY --chown=django:django ./.env.test .env

CMD ["start-dev-server.sh"]


####################
# PRODUCTION IMAGE #
####################
FROM base as prod

USER root

COPY --chown=django:django ./.env.prod .env
COPY --chown=django:django ./requirements/prod.txt requirements/prod.txt
COPY --chown=django:django ./docker/start-prod-server.sh /usr/local/bin/start-prod-server.sh

RUN chmod +x /usr/local/bin/start-prod-server.sh
RUN pip install --no-cache-dir -r requirements/prod.txt

USER django

CMD ["start-prod-server.sh"]
