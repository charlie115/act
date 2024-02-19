# Start from the Python 3.9 image
FROM python:3.9

# Update the package list
RUN apt-get update

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

# Copy the info_core
COPY trade_core /home/trade_core

# Install requirements.txt
RUN pip3.9 install -r /home/trade_core/requirements.txt

# Move to /home/trade_core
WORKDIR /home/trade_core/api

# Start Gunicorn with Uvicorn workers
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]