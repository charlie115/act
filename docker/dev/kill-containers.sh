CURRENT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )
BASE_DIR=$(dirname $(dirname "$CURRENT_DIR"))

source $BASE_DIR/scripts/cecho.sh


echo "${BCYAN}Stopping and removing docker containers...${SET}"
echo
docker compose down -v
