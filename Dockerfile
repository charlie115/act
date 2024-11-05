# Start from the Python 3.9 image
FROM python:3.10 AS base

# # FOR Google Chrome
# RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - 
# RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'

# Install system dependencies for building Python packages with C extensions
RUN apt-get update

# # Install Google Chrome
# RUN apt-get install -y google-chrome-stable

# Install Node.js and npm
# We'll use a specific version of Node.js for reliability
RUN apt-get install -y curl gnupg
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
RUN apt-get install -y nodejs
RUN apt-get install -y npm

# Verify if Node.js and npm are installed
RUN node --version
RUN npm --version

# Install PM2 globally
RUN npm install pm2 -g

# Install Redis
RUN apt-get install -y redis-server
# Start Redis server
CMD redis-server

# Set WORKDIR
WORKDIR /home/info_core/

# Copy the info_core
COPY info_core info_core/

# Copy the requirements.txt
COPY ./requirements.txt requirements.txt

# Update pip
RUN pip install --upgrade pip

# Install requirements.txt
RUN pip install -r requirements.txt


#############
# DEV IMAGE #
#############
FROM base AS dev

COPY ./docker/start-dev-service.sh /usr/local/bin/start-dev-service.sh
COPY ./.env.dev .env

CMD ["start-dev-service.sh"]

#############
# TEST IMAGE #
#############
FROM base AS test

COPY ./docker/start-test-service.sh /usr/local/bin/start-test-service.sh
COPY ./.env.test .env

CMD ["start-test-service.sh"]

##############
# PROD IMAGE #
##############
FROM base AS prod

COPY ./docker/start-prod-service.sh /usr/local/bin/start-prod-service.sh
COPY ./.env.prod .env

CMD ["start-prod-service.sh"]