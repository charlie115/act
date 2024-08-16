# Community DRF

This project is the backend for arbitrage community using django and drf. It contains the logic for all community related especially apps that are connected to Users. 

This project also provides the APIs for the frontend, and acts as the middleman between frontend and core projects.

---

## Development

You can develop and run server directly, or run it in docker container.


#### Run directly ####

1. Create virtual environment.
2. Install requirements.
3. For first time development, you have to run migrations.
    ```
    python manage.py migrate
    ```
4. Run server. 
    ```
    python manage.py runserver
    ```

#### Run docker container ####

1. Prepare `.env.dev` file. See `.env.example`.
2. Build and run.
    ```
    docker compose up --build -d
    ```


Project is live at http://127.0.0.1:8000/.  
Django admin is available at http://127.0.0.1:8000/admin/.

---


### Deployment ###

This project is deployed as a docker container. You can check the Dockerfile for more information if you want to know the detailed steps.

This container is deployed to the prod together with other [arbitrage_community](https://bitbucket.org/arbitrage-community-website/arbitrage_community/) projects. But before that, we have to build the image for this project so it can be included in [arbitrage_community](https://bitbucket.org/arbitrage-community-website/arbitrage_community/) deployment.

We normally build images in the server itself. So first, we place our source code in the server (under `/opt/`), then we build the image.

1. Go to project directory.
    ```
    cd /opt/community_drf
    ```
    *Clone the repository if it doesn't exist yet.*

2. Build the appropriate image. Along with community_drf, we also have to build images for celery beat and worker.  
    * Test
        ```
        docker build . --target test -t community-drf:test
        docker build . --target test -t community-celery-worker:test
        docker build . --target test -t community-celery-beat:test
        ```
    * Production
        ```
        docker build . --target prod -t community-drf
        docker build . --target prod -t community-celery-worker
        docker build . --target prod -t community-celery-beat
        ```

    * Image name for test environment:
        * `community-drf:test`
        * `community-celery-worker:test`
        * `community-celery-beat:test`
    * Image name for production:
        * `community-drf`
        * `community-celery-worker`
        * `community-celery-beat`
        * Which is the same as 
            * `community-drf:latest`
            * `community-celery-worker:latest`
            * `community-celery-beat:latest`

Then it's good to go. Container will be up once `docker compose up` is run in [arbitrage_community](https://bitbucket.org/arbitrage-community-website/arbitrage_community/).
