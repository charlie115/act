#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
MANIFEST_PATH="${SCRIPT_DIR}/repos.manifest"
DEFAULT_DESTINATION="${WORKSPACE_ROOT}/../acw-monorepo"
ALLOW_DIRTY="${ALLOW_DIRTY:-0}"
CHECK_ONLY=0
OVERLAY_WORKING_TREE=0

usage() {
  cat <<'EOF'
Usage:
  ./scripts/monorepo/create_monorepo.sh --check
  ./scripts/monorepo/create_monorepo.sh [--overlay-working-tree] [destination]

Options:
  --check                 Validate workspace state without creating the monorepo
  --overlay-working-tree  Copy current dirty working tree files after history import

Environment:
  ALLOW_DIRTY=1   Allow import even if nested repositories have uncommitted changes

Notes:
  - The script creates a new root repository in a separate destination directory.
  - History is preserved using merge + read-tree, without requiring git subtree.
  - By default, the script refuses to continue if any nested repository is dirty.
  - With --overlay-working-tree, dirty repositories are allowed and their current files
    are copied into the destination after import.
EOF
}

require_command() {
  local command_name="$1"

  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "Missing required command: ${command_name}" >&2
    exit 1
  fi
}

is_repo_dirty() {
  local repo_dir="$1"
  [[ -n "$(git -C "${repo_dir}" status --porcelain)" ]]
}

check_manifest() {
  if [[ ! -f "${MANIFEST_PATH}" ]]; then
    echo "Manifest file not found: ${MANIFEST_PATH}" >&2
    exit 1
  fi
}

check_repo_cleanliness() {
  local repo_name="$1"
  local repo_dir="$2"
  local current_branch
  local dirty

  if [[ ! -d "${repo_dir}/.git" ]]; then
    echo "Repository is missing .git directory: ${repo_name}" >&2
    return 1
  fi

  current_branch="$(git -C "${repo_dir}" branch --show-current)"
  dirty="$(git -C "${repo_dir}" status --porcelain)"

  echo "[${repo_name}] branch=${current_branch:-detached}"

  if [[ -n "${dirty}" ]]; then
    echo "  dirty=yes"
    if [[ "${ALLOW_DIRTY}" != "1" ]]; then
      echo "  error=workspace has uncommitted changes" >&2
      return 1
    fi
  else
    echo "  dirty=no"
  fi

  return 0
}

copy_scaffold() {
  local destination="$1"

  mkdir -p "${destination}/docs/architecture"
  mkdir -p "${destination}/scripts/monorepo"

  cp "${WORKSPACE_ROOT}/README.md" "${destination}/README.md"
  cp "${WORKSPACE_ROOT}/.gitignore" "${destination}/.gitignore"
  cp "${WORKSPACE_ROOT}/docs/architecture/service-dependency-map.md" \
    "${destination}/docs/architecture/service-dependency-map.md"
  cp "${WORKSPACE_ROOT}/docs/architecture/monorepo-migration-plan.md" \
    "${destination}/docs/architecture/monorepo-migration-plan.md"
  cp "${WORKSPACE_ROOT}/scripts/monorepo/repos.manifest" \
    "${destination}/scripts/monorepo/repos.manifest"
  cp "${WORKSPACE_ROOT}/scripts/monorepo/create_monorepo.sh" \
    "${destination}/scripts/monorepo/create_monorepo.sh"

  chmod +x "${destination}/scripts/monorepo/create_monorepo.sh"
}

initialize_destination_repo() {
  local destination="$1"

  if [[ -e "${destination}" ]]; then
    if [[ -n "$(find "${destination}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
      echo "Destination already exists and is not empty: ${destination}" >&2
      exit 1
    fi
  else
    mkdir -p "${destination}"
  fi

  git init "${destination}" >/dev/null
  copy_scaffold "${destination}"
  git -C "${destination}" add README.md .gitignore docs scripts
  git -C "${destination}" commit -m "chore: initialize ACW monorepo scaffold" >/dev/null
}

import_repo() {
  local destination="$1"
  local source_repo="$2"
  local target_prefix="$3"
  local branch="$4"
  local remote_name="import_${source_repo}"
  local source_path="${WORKSPACE_ROOT}/${source_repo}"

  echo "Importing ${source_repo} -> ${target_prefix} (${branch})"

  git -C "${destination}" remote add "${remote_name}" "${source_path}"
  git -C "${destination}" fetch "${remote_name}" "${branch}" >/dev/null
  git -C "${destination}" merge -s ours --no-commit --allow-unrelated-histories \
    "${remote_name}/${branch}" >/dev/null
  git -C "${destination}" read-tree --prefix="${target_prefix}/" -u "${remote_name}/${branch}"
  git -C "${destination}" commit -m "chore: import ${source_repo} into ${target_prefix}" >/dev/null
  git -C "${destination}" remote remove "${remote_name}"
}

overlay_working_tree() {
  local destination="$1"
  local source_repo="$2"
  local target_prefix="$3"
  local source_path="${WORKSPACE_ROOT}/${source_repo}"
  local target_path="${destination}/${target_prefix}"

  if ! is_repo_dirty "${source_path}"; then
    return 0
  fi

  echo "Overlaying dirty working tree for ${source_repo} -> ${target_prefix}"

  mkdir -p "${target_path}"

  rsync -a \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='build' \
    --exclude='dist' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='.mypy_cache' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='logs' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='*.log' \
    --exclude='dump.rdb' \
    --exclude='.env' \
    --exclude='.env.*' \
    --exclude='.DS_Store' \
    "${source_path}/" "${target_path}/"

  git -C "${destination}" add "${target_prefix}"
  git -C "${destination}" commit -m "chore: overlay working tree from ${source_repo}" >/dev/null || true
}

run_preflight() {
  local source_repo
  local target_prefix
  local branch
  local kind
  local failures=0

  echo "Workspace root: ${WORKSPACE_ROOT}"
  echo "Manifest: ${MANIFEST_PATH}"

  while IFS='|' read -r source_repo target_prefix branch kind; do
    [[ -z "${source_repo}" || "${source_repo}" == \#* ]] && continue
    if ! check_repo_cleanliness "${source_repo}" "${WORKSPACE_ROOT}/${source_repo}"; then
      failures=$((failures + 1))
    fi
  done < "${MANIFEST_PATH}"

  if [[ "${failures}" -gt 0 ]]; then
    echo "Preflight failed: ${failures} repository check(s) need attention." >&2
    return 1
  fi
}

main() {
  local destination="${DEFAULT_DESTINATION}"
  local source_repo
  local target_prefix
  local branch
  local kind

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --help|-h)
        usage
        exit 0
        ;;
      --check)
        CHECK_ONLY=1
        shift
        ;;
      --overlay-working-tree)
        OVERLAY_WORKING_TREE=1
        ALLOW_DIRTY=1
        shift
        ;;
      *)
        destination="$1"
        shift
        ;;
    esac
  done

  require_command git
  require_command rsync
  check_manifest
  run_preflight

  if [[ "${CHECK_ONLY}" == "1" ]]; then
    echo "Preflight check passed."
    exit 0
  fi

  initialize_destination_repo "${destination}"

  while IFS='|' read -r source_repo target_prefix branch kind; do
    [[ -z "${source_repo}" || "${source_repo}" == \#* ]] && continue
    import_repo "${destination}" "${source_repo}" "${target_prefix}" "${branch}"
  done < "${MANIFEST_PATH}"

  if [[ "${OVERLAY_WORKING_TREE}" == "1" ]]; then
    while IFS='|' read -r source_repo target_prefix branch kind; do
      [[ -z "${source_repo}" || "${source_repo}" == \#* ]] && continue
      overlay_working_tree "${destination}" "${source_repo}" "${target_prefix}"
    done < "${MANIFEST_PATH}"
  fi

  echo "Monorepo created at: ${destination}"
  echo "Next step: review imported layout and then archive or remove nested .git directories in the old workspace only after validation."
}

main "$@"
