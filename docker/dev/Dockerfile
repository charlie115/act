FROM python:3.10

WORKDIR /community_drf

# From least edited to frequent to avoid rebuilding image caches
COPY ./manage.py /community_drf/manage.py

COPY ./.env.dev /community_drf/.env

COPY ./requirements/ /community_drf/requirements/
RUN pip install -r requirements/dev.txt

COPY ./config /community_drf/config/
COPY ./lib /community_drf/lib/
COPY ./apps /community_drf/apps/

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]