# NewsCore #

This project scrapes crypto news, sns and announcements posts and store data in a separate postgres db. You can view these data in Arbicrypto News tab.

We currently source them from the following media:

* News - scrapes every minute
    * zdnet
    * etoday
    * einfomax
    * bonmedia
    * fnnews
    * decenter
    * blockstreet
    * coindeskkorea
    * coinreaders
    * blockmedia

* SNS - scrapes every 10 minutes  
    * X (Twitter) - however, since Elon limited public x data, we get it from Nitter instead

* Announcement - scrapes every hour  
    * UPbit
    * Bithumb
    * OKX
    * Bybit
    * Binance



### Development ###

You can run and test the app by running it directly, or running the docker container.

#### Run directly ####

1. Create virtual environment.
2. Install requirements.
3. You can run the scripts inside `scripts/` folder or manually run scrapy crawl commands.

#### Run docker container ####

1. Prepare `.env.dev` file. See `.env.example`.
2. Build and run.
    ```
    docker compose up --build -d
    ```

### Deployment ###

This project is deployed as a docker container. You can check the Dockerfile for more information if you want to know the detailed steps.


This container is deployed to the prod together with other [arbitrage_community](https://bitbucket.org/arbitrage-community-website/arbitrage_community/) projects. But before that, we have to build the image for this project so it can be included in [arbitrage_community](https://bitbucket.org/arbitrage-community-website/arbitrage_community/) deployment.

We normally build images in the server itself. So first, we place our source code in the server (under `/opt/`), then we build the image.

1. Go to project directory.
    ```
    cd /opt/news_core
    ```
    *Clone the repository if it doesn't exist yet.*

2. Build the appropriate image.
    ```
    docker build . --target {env} -t {image-name}
    ```

    * Image name for test environment: `news-core:test`
    * Image name for production: `news-core`
        * *(Which is the same as `news-core:latest`)*

Then it's good to go. Container will be up once `docker compose up` is run in [arbitrage_community](https://bitbucket.org/arbitrage-community-website/arbitrage_community/).