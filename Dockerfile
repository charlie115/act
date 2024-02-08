##############
# BASE IMAGE #
##############
FROM python:3.10 as base

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt install -y cron nano

WORKDIR /home/scrapy/news_core/

COPY ./scrapy.cfg scrapy.cfg
COPY ./requirements.txt requirements.txt
COPY ./scripts scripts/
COPY ./news_core news_core/

RUN mkdir logs

RUN pip install --no-cache-dir -r requirements.txt


#############
# DEV IMAGE #
#############
FROM base as dev

COPY ./.env.dev .env

RUN crontab /home/scrapy/news_core/scripts/cron_test

CMD ["cron", "-f"]


#############
# TEST IMAGE #
#############
FROM base as test

COPY ./.env.test .env

RUN crontab /home/scrapy/news_core/scripts/cron_test

CMD ["cron", "-f"]


##############
# PROD IMAGE #
##############
FROM base as prod

COPY ./.env.prod .env

RUN crontab /home/scrapy/news_core/scripts/cron

CMD ["cron", "-f"]
