#!/bin/bash

WORKING_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )
ENV_FILE="$WORKING_DIR"/.env

if [ -e "$ENV_FILE" ]
then
    source $ENV_FILE

    echo "Setting up redis.conf ..."
    cat $WORKING_DIR/redis/conf/redis.conf >> $HOME/community-redis/conf/redis.conf
    bash -c 'cat <<EOF >>'$HOME/community-redis/conf/redis.conf'

# Credentials
requirepass '$REDIS_PASSWORD'

EOF'
    echo
else
  echo "Please prepare your .env file first."
  echo
fi


