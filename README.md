# Arbitrage Community #

Setups the full arbitrage community system:
* Nginx and Certbot
* Databases
* Frontend
* Backend (community and cores)

Different environments are separated into folders since each environments can have different setups. This is also to isolate environments from each other to avoid mixing them up or any dependency issues.  

As you can see in the respective (testing, production) docker compose files, the container names always have the environment as their prefix to avoid any accidents when operating on the containers.

List of containers:

* certbot
* test-community-nginx
* test-community-postgres
* test-community-redis
* test-community-mongodb
* test-community-drf
* test-community-celery-worker
* test-community-celery-beat
* test-news-core
* test-info-core

Prod containers have the same list with ***prod*** as prefix.

### Deployment ###

Since this project is basically a configuration of a docker compose with multi-containers, deploying is simply just running docker compose. 

However, we separated testing and production environments. 

1. So first, you have to go to the environment folder before running these commands to make sure that you are executing commands for that environment.
	```
	cd testing
	```
2. Then setup env variables according to the environment. See `.env.example`.
	```
	cp .env.example .env
	```

3. To start the containers: 
	```
	docker compose up --build -d
	```

#### Note

If you check the docker compose file, one thing to note is that there is no step specified for building images except for Nginx. This means that either the images must exist locally already, or an image can just be pulled online. 

For our own projects, these images must already exist before we start `docker compose up`. The person-in-charge for these projects must be responsible for deploying (building images) of these projects. Then the docker compose should work as expected once all images are available.

#### Other helpful commands

##### To stop and remove all containers: 
```
docker compose down -v
```

You can also start/stop a specific container by providing the **service name** defined in docker compose. For example:
```
docker compose up drf --build -d
docker compose down drf -v
```

##### To enter containers:
* drf, celery, postgres, mongodb, news-core
    * `docker exec -it {container-name} bash`
* nginx, redis _(These images don't have bash)_
    * `docker exec -it {container-name} sh`  

