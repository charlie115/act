CURRENT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )
BASE_DIR=$(dirname $(dirname "$CURRENT_DIR"))

source $BASE_DIR/scripts/cecho.sh

# Copy .dockerignore

# Check .env.dev for the django project
if [ ! -f $BASE_DIR/.env.dev ]; then
    echo
    echo "${RED}.env.dev${SET} file not found."
    echo "Check $BASE_DIR/.env.example and prepare your ${RED}$BASE_DIR/.env.dev${SET} file first."
    echo
    exit
fi

# Check .env for the docker compose
if [ ! -f $BASE_DIR/docker/dev/.env ]; then
    echo
    echo "${RED}.env${SET} file not found."
    echo "Check .env.example and prepare ${RED}.env${SET} file for the docker compose first."
    echo
    exit
fi

# Build and run containers
docker compose up --build -d

# Migrate migrations
docker exec -it dev-community-drf python manage.py migrate

# Create superuser
echo && echo "${BCYAN}Create superuser?${SET} y/Y"
read create_superuser
if [[ "$create_superuser" == "y" ]] || [[ "$create_superuser" == "Y" ]]; then
    docker exec -it dev-community-drf python manage.py createsuperuser
fi