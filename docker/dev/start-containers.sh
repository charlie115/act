CURRENT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )
BASE_DIR=$(dirname $(dirname "$CURRENT_DIR"))

source $BASE_DIR/scripts/cecho.sh


echo
echo "${BCYAN}[1/6] Checking .env for docker compose...${SET}"
if [ ! -f $BASE_DIR/docker/dev/.env ]; then
    echo "  ${RED}.env${SET} file for ${BRED}docker compose${SET} not found."
    echo "  Check ./.env.example and prepare ${RED}./.env${SET} file for the docker compose first."
    echo
    exit
fi


echo
echo "${BCYAN}[2/6] Checking .env.dev for the django project...${SET}"
if [ ! -f $BASE_DIR/.env.dev ]; then
    echo "  ${RED}.env.dev${SET} file for ${BRED}django project${SET} not found."
    echo "  Check $BASE_DIR/.env.example"
    echo "  and create ${RED}$BASE_DIR/.env.dev${SET} first."
    echo
    exit
fi


echo
echo "${BCYAN}[3/6] Creating directory for postgres data...${SET}"
mkdir -p $HOME/dev-community-db


echo
echo "${BCYAN}[4/6] Building and running docker containers...${SET}"
docker compose up --build -d


echo
echo "${BCYAN}[5/6] Migrating django migrations to the database...${SET}"
echo
docker exec -it dev-community-drf python manage.py migrate


echo
echo "${BCYAN}[6/6] Creating superuser...${SET}"
echo
echo "${BCYAN}Create superuser?${SET} y/Y"
read create_superuser
if [[ "$create_superuser" == "y" ]] || [[ "$create_superuser" == "Y" ]]; then
    docker exec -it dev-community-drf python manage.py createsuperuser
fi
