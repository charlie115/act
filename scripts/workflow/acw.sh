#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

require_command() {
  local command_name="$1"
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "Missing required command: ${command_name}" >&2
    exit 1
  fi
}

frontend_runner() {
  if command -v pnpm >/dev/null 2>&1; then
    echo "pnpm"
    return 0
  fi

  if command -v corepack >/dev/null 2>&1; then
    echo "corepack pnpm"
    return 0
  fi

  echo ""
  return 1
}

copy_template() {
  local src="$1"
  local dest="$2"
  local force="${3:-0}"

  if [[ ! -f "${src}" ]]; then
    return 0
  fi

  if [[ -f "${dest}" && "${force}" != "1" ]]; then
    echo "skip ${dest}"
    return 0
  fi

  mkdir -p "$(dirname "${dest}")"
  cp "${src}" "${dest}"
  echo "write ${dest}"
}

normalize_env() {
  local env_name="$1"

  case "${env_name}" in
    testing|test)
      echo "testing"
      ;;
    production|prod)
      echo "production"
      ;;
    dev|development)
      echo "dev"
      ;;
    *)
      echo "Unsupported environment: ${env_name}" >&2
      exit 1
      ;;
  esac
}

docker_target_for_service_env() {
  local env_name="$1"

  case "${env_name}" in
    dev)
      echo "dev"
      ;;
    testing)
      echo "test"
      ;;
    production)
      echo "prod"
      ;;
  esac
}

docker_suffix_for_stack_env() {
  local env_name="$1"

  case "${env_name}" in
    dev)
      echo ":dev"
      ;;
    testing)
      echo ":test"
      ;;
    production)
      echo ""
      ;;
  esac
}

compose_env_dir() {
  local env_name="$1"

  case "${env_name}" in
    dev)
      echo "dev"
      ;;
    testing)
      echo "testing"
      ;;
    production)
      echo "production"
      ;;
    *)
      echo "Compose stack supports only testing or production: ${env_name}" >&2
      exit 1
      ;;
  esac
}

compose_dir() {
  local stack="$1"
  local env_name="$2"
  echo "${ROOT_DIR}/infra/compose/${stack}/$(compose_env_dir "${env_name}")"
}

compose_stack_root() {
  local stack="$1"
  echo "${ROOT_DIR}/infra/compose/${stack}"
}

compose_command_prefix() {
  local stack="$1"
  local env_name="$2"
  local stack_root env_dir

  stack_root="$(compose_stack_root "${stack}")"
  env_dir="$(compose_env_dir "${env_name}")"

  if [[ -f "${stack_root}/compose.base.yml" && -f "${stack_root}/compose.${env_name}.yml" ]]; then
    printf '%s\0' \
      docker compose \
      --env-file "${stack_root}/${env_dir}/.env" \
      -f "${stack_root}/compose.base.yml" \
      -f "${stack_root}/compose.${env_name}.yml"
    return 0
  fi

  printf '%s\0' docker compose
}

build_community_images() {
  local env_name="$1"
  local target suffix

  target="$(docker_target_for_service_env "${env_name}")"
  suffix="$(docker_suffix_for_stack_env "${env_name}")"

  echo "Building community images for ${env_name}"

  docker build "${ROOT_DIR}/apps/community_drf" --target "${target}" -t "community-drf${suffix}"
  docker build "${ROOT_DIR}/apps/community_drf" --target "${target}" -t "community-celery-worker${suffix}"
  docker build "${ROOT_DIR}/apps/community_drf" --target "${target}" -t "community-celery-beat${suffix}"
  if [[ "${env_name}" != "dev" ]]; then
    docker build "${ROOT_DIR}/apps/community_web_next" -t "community-web-next${suffix}"
  fi
  docker build "${ROOT_DIR}/services/news_core" --target "${target}" -t "news-core${suffix}"
  docker build -f "${ROOT_DIR}/services/info_core/Dockerfile" "${ROOT_DIR}" --target "${target}" -t "info-core${suffix}"
}

build_trade_images() {
  local env_name="$1"
  local target suffix api_target

  target="$(docker_target_for_service_env "${env_name}")"
  suffix="$(docker_suffix_for_stack_env "${env_name}")"

  case "${env_name}" in
    dev)
      api_target="api_dev"
      ;;
    testing)
      api_target="api_test"
      ;;
    production)
      api_target="api_prod"
      ;;
  esac

  echo "Building trade images for ${env_name}"

  docker build -f "${ROOT_DIR}/services/trade_core/Dockerfile" "${ROOT_DIR}" --target "${target}" -t "trade-core${suffix}"
  docker build -f "${ROOT_DIR}/services/trade_core/Dockerfile" "${ROOT_DIR}" --target "${api_target}" -t "trade-core-api${suffix}"
}

build_web() {
  local env_name="$1"
  local runner
  local env_file

  runner="$(frontend_runner || true)"
  if [[ -z "${runner}" ]]; then
    echo "pnpm or corepack is required for community_web_next builds." >&2
    exit 1
  fi

  case "${env_name}" in
    testing)
      env_file=".env.testing"
      ;;
    production)
      env_file=".env.production"
      ;;
    *)
      echo "community_web_next build supports only testing or production: ${env_name}" >&2
      exit 1
      ;;
  esac

  echo "Building community_web_next for ${env_name}"

  (
    cd "${ROOT_DIR}/apps/community_web_next"
    eval "${runner} install"
    set -a
    source "${env_file}"
    set +a
    eval "${runner} run build"
  )
}

sync_web() {
  local env_name="$1"
  echo "sync-web is not required for official Next.js frontend (${env_name})."
}

stack_command() {
  local stack="$1"
  local env_name="$2"
  local action="$3"
  shift 3

  local dir stack_root env_dir
  local compose_cmd=()

  stack_root="$(compose_stack_root "${stack}")"
  env_dir="$(compose_env_dir "${env_name}")"
  dir="$(compose_dir "${stack}" "${env_name}")"

  while IFS= read -r -d '' item; do
    compose_cmd+=("${item}")
  done < <(compose_command_prefix "${stack}" "${env_name}")

  if [[ "${#compose_cmd[@]}" -gt 2 ]]; then
    dir="${stack_root}"
  fi

  case "${action}" in
    up)
      (cd "${dir}" && "${compose_cmd[@]}" up --build -d "$@")
      ;;
    down)
      (cd "${dir}" && "${compose_cmd[@]}" down -v "$@")
      ;;
    *)
      (cd "${dir}" && "${compose_cmd[@]}" "${action}" "$@")
      ;;
  esac
}

workflow_help() {
  cat <<'EOF'
ACW workflow commands

Usage:
  ./scripts/workflow/acw.sh doctor
  ./scripts/workflow/acw.sh env-init [--force]
  ./scripts/workflow/acw.sh build-images <community|trade|all> <dev|testing|production>
  ./scripts/workflow/acw.sh build-web <testing|production>
  ./scripts/workflow/acw.sh web-dev
  ./scripts/workflow/acw.sh sync-web <testing|production>
  ./scripts/workflow/acw.sh stack <community|trade> <dev|testing|production> <up|down|ps|logs|restart|config> [extra args...]
  ./scripts/workflow/acw.sh dev-up <community|trade|all>
  ./scripts/workflow/acw.sh dev-down <community|trade|all>
  ./scripts/workflow/acw.sh prod-up <community|trade|all>
  ./scripts/workflow/acw.sh prod-down <community|trade|all>

Examples:
  make env-init
  make build-images STACK=all ENV=testing
  make build-web ENV=testing
  make web-dev
  make dev-up STACK=all
  make stack STACK=community ENV=testing ACTION=logs ARGS="drf -f"
EOF
}

doctor() {
  local runner

  require_command docker
  require_command rsync
  runner="$(frontend_runner || true)"

  echo "docker: $(command -v docker)"
  echo "rsync: $(command -v rsync)"
  if docker compose version >/dev/null 2>&1; then
    echo "docker compose: available"
  else
    echo "docker compose: missing" >&2
    exit 1
  fi

  if [[ -n "${runner}" ]]; then
    echo "frontend package runner: ${runner}"
  else
    echo "frontend package runner: missing (pnpm or corepack required)" >&2
  fi

  for path in \
    "${ROOT_DIR}/apps/community_drf/.env.dev" \
    "${ROOT_DIR}/apps/community_drf/.env.test" \
    "${ROOT_DIR}/apps/community_drf/.env.prod" \
    "${ROOT_DIR}/services/info_core/.env.dev" \
    "${ROOT_DIR}/services/info_core/.env.test" \
    "${ROOT_DIR}/services/info_core/.env.prod" \
    "${ROOT_DIR}/services/news_core/.env.dev" \
    "${ROOT_DIR}/services/news_core/.env.test" \
    "${ROOT_DIR}/services/news_core/.env.prod" \
    "${ROOT_DIR}/services/trade_core/.env.dev" \
    "${ROOT_DIR}/services/trade_core/.env.test" \
    "${ROOT_DIR}/services/trade_core/.env.prod" \
    "${ROOT_DIR}/apps/community_web_next/.env.development" \
    "${ROOT_DIR}/apps/community_web_next/.env.testing" \
    "${ROOT_DIR}/apps/community_web_next/.env.production" \
    "${ROOT_DIR}/infra/compose/community/dev/.env" \
    "${ROOT_DIR}/infra/compose/community/testing/.env" \
    "${ROOT_DIR}/infra/compose/community/production/.env" \
    "${ROOT_DIR}/infra/compose/trade/testing/.env" \
    "${ROOT_DIR}/infra/compose/trade/production/.env"; do
    if [[ -f "${path}" ]]; then
      echo "ok  ${path#${ROOT_DIR}/}"
    else
      echo "miss ${path#${ROOT_DIR}/}"
    fi
  done
}

env_init() {
  local force=0

  if [[ "${1:-}" == "--force" ]]; then
    force=1
  fi

  copy_template "${ROOT_DIR}/apps/community_drf/.env.example" "${ROOT_DIR}/apps/community_drf/.env.dev" "${force}"
  copy_template "${ROOT_DIR}/apps/community_drf/.env.example" "${ROOT_DIR}/apps/community_drf/.env.test" "${force}"
  copy_template "${ROOT_DIR}/apps/community_drf/.env.example" "${ROOT_DIR}/apps/community_drf/.env.prod" "${force}"

  copy_template "${ROOT_DIR}/services/info_core/.env.example" "${ROOT_DIR}/services/info_core/.env.dev" "${force}"
  copy_template "${ROOT_DIR}/services/info_core/.env.example" "${ROOT_DIR}/services/info_core/.env.test" "${force}"
  copy_template "${ROOT_DIR}/services/info_core/.env.example" "${ROOT_DIR}/services/info_core/.env.prod" "${force}"

  copy_template "${ROOT_DIR}/services/news_core/.env.example" "${ROOT_DIR}/services/news_core/.env.dev" "${force}"
  copy_template "${ROOT_DIR}/services/news_core/.env.example" "${ROOT_DIR}/services/news_core/.env.test" "${force}"
  copy_template "${ROOT_DIR}/services/news_core/.env.example" "${ROOT_DIR}/services/news_core/.env.prod" "${force}"

  copy_template "${ROOT_DIR}/services/trade_core/.env.example" "${ROOT_DIR}/services/trade_core/.env.dev" "${force}"
  copy_template "${ROOT_DIR}/services/trade_core/.env.example" "${ROOT_DIR}/services/trade_core/.env.test" "${force}"
  copy_template "${ROOT_DIR}/services/trade_core/.env.example" "${ROOT_DIR}/services/trade_core/.env.prod" "${force}"

  copy_template "${ROOT_DIR}/apps/community_web/.env.test.example" "${ROOT_DIR}/apps/community_web/.env.test" "${force}"
  copy_template "${ROOT_DIR}/apps/community_web/.env.production.example" "${ROOT_DIR}/apps/community_web/.env.production" "${force}"
  copy_template "${ROOT_DIR}/apps/community_web_next/.env.example" "${ROOT_DIR}/apps/community_web_next/.env.development" "${force}"
  copy_template "${ROOT_DIR}/apps/community_web_next/.env.example" "${ROOT_DIR}/apps/community_web_next/.env.testing" "${force}"
  copy_template "${ROOT_DIR}/apps/community_web_next/.env.example" "${ROOT_DIR}/apps/community_web_next/.env.production" "${force}"

  copy_template "${ROOT_DIR}/infra/compose/community/dev/.env.example" "${ROOT_DIR}/infra/compose/community/dev/.env" "${force}"
  copy_template "${ROOT_DIR}/infra/compose/community/testing/nginx/watch_certs.sh" "${HOME}/dev-community-nginx/watch_certs.sh" "${force}"
  copy_template "${HOME}/test-community-redis/conf/redis.conf" "${HOME}/dev-community-redis/conf/redis.conf" "${force}"
  copy_template "${ROOT_DIR}/infra/compose/community/testing/.env.example" "${ROOT_DIR}/infra/compose/community/testing/.env" "${force}"
  copy_template "${ROOT_DIR}/infra/compose/community/production/.env.example" "${ROOT_DIR}/infra/compose/community/production/.env" "${force}"
  copy_template "${ROOT_DIR}/infra/compose/trade/testing/.env.example" "${ROOT_DIR}/infra/compose/trade/testing/.env" "${force}"
  copy_template "${ROOT_DIR}/infra/compose/trade/production/.env.example" "${ROOT_DIR}/infra/compose/trade/production/.env" "${force}"

  mkdir -p "${HOME}/dev-community-secrets"
  if [[ ! -f "${HOME}/dev-community-secrets/hd_mnemonic.txt" || "${force}" == "1" ]]; then
    printf 'test mnemonic\n' > "${HOME}/dev-community-secrets/hd_mnemonic.txt"
    echo "write ${HOME}/dev-community-secrets/hd_mnemonic.txt"
  fi
}

build_images() {
  local stack="$1"
  local env_name
  env_name="$(normalize_env "$2")"

  case "${stack}" in
    community)
      build_community_images "${env_name}"
      ;;
    trade)
      build_trade_images "${env_name}"
      ;;
    all)
      build_community_images "${env_name}"
      build_trade_images "${env_name}"
      ;;
    *)
      echo "Unsupported stack: ${stack}" >&2
      exit 1
      ;;
  esac
}

web_dev() {
  local runner

  runner="$(frontend_runner || true)"
  if [[ -z "${runner}" ]]; then
    echo "pnpm or corepack is required for community_web_next dev server." >&2
    exit 1
  fi

  echo "Starting community_web_next local dev server"

  (
    cd "${ROOT_DIR}/apps/community_web_next"
    eval "${runner} install"
    set -a
    source ".env.development"
    set +a
    eval "${runner} run dev -- --hostname 0.0.0.0 --port 3000"
  )
}

dev_up() {
  local stack="${1:-all}"

  env_init

  case "${stack}" in
    community)
      build_images community dev
      stack_command community dev up
      ;;
    trade)
      build_images trade testing
      stack_command trade testing up
      ;;
    all)
      build_images community dev
      build_images trade testing
      stack_command community dev up
      stack_command trade testing up
      ;;
    *)
      echo "Unsupported stack: ${stack}" >&2
      exit 1
      ;;
  esac
}

dev_down() {
  local stack="${1:-all}"

  case "${stack}" in
    community)
      stack_command community dev down
      ;;
    trade)
      stack_command trade testing down
      ;;
    all)
      stack_command community dev down
      stack_command trade testing down
      ;;
    *)
      echo "Unsupported stack: ${stack}" >&2
      exit 1
      ;;
  esac
}

prod_up() {
  local stack="${1:-all}"

  env_init

  case "${stack}" in
    community)
      build_images community production
      stack_command community production up
      ;;
    trade)
      build_images trade production
      stack_command trade production up
      ;;
    all)
      build_images all production
      stack_command community production up
      stack_command trade production up
      ;;
    *)
      echo "Unsupported stack: ${stack}" >&2
      exit 1
      ;;
  esac
}

prod_down() {
  local stack="${1:-all}"

  case "${stack}" in
    community)
      stack_command community production down
      ;;
    trade)
      stack_command trade production down
      ;;
    all)
      stack_command community production down
      stack_command trade production down
      ;;
    *)
      echo "Unsupported stack: ${stack}" >&2
      exit 1
      ;;
  esac
}

main() {
  local command="${1:-help}"
  shift || true

  case "${command}" in
    help)
      workflow_help
      ;;
    doctor)
      doctor
      ;;
    env-init)
      env_init "$@"
      ;;
    build-images)
      build_images "$@"
      ;;
    build-web)
      build_web "$(normalize_env "$1")"
      ;;
    web-dev)
      web_dev
      ;;
    sync-web)
      sync_web "$(normalize_env "$1")"
      ;;
    stack)
      stack_command "$1" "$(normalize_env "$2")" "$3" "${@:4}"
      ;;
    dev-up)
      dev_up "$@"
      ;;
    dev-down)
      dev_down "$@"
      ;;
    prod-up)
      prod_up "$@"
      ;;
    prod-down)
      prod_down "$@"
      ;;
    *)
      echo "Unknown command: ${command}" >&2
      workflow_help
      exit 1
      ;;
  esac
}

main "$@"
