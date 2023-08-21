# README #

Setups the full arbitrage community app including the nginx, frontend, backend, core, etc.

Contains multiple docker containers:  

* **community-nginx**
* **community-drf**
* **info_core** (to be added later)

To start running the containers:
```
docker compose up --build -d
```

To enter the containers:

* **community-drf**: `docker exec -it community-drf bash`
* **community-nginx**: `docker exec -it community-nginx /bin/sh --login`  
	_(Since it is an alpine image and doesn't have bash)_

---
Update me later...

### What is this repository for? ###

* Quick summary
* Version
* [Learn Markdown](https://bitbucket.org/tutorials/markdowndemo)

### How do I get set up? ###

* Summary of set up
* Configuration
* Dependencies
* Database configuration
* How to run tests
* Deployment instructions

### Contribution guidelines ###

* Writing tests
* Code review
* Other guidelines

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact