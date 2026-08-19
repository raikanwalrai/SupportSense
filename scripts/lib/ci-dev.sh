#!/usr/bin/env bash

# ============================================================
# SupportSense Development Environment
# GITHUB ACTIONS CI SCRIPT
# ============================================================
#
# Provides developer-friendly access to GitHub Actions CI.
#
# Commands:
#
#   ci
#       Watch the latest CI run for the current branch.
#
#   ci status
#       Show the latest CI run without waiting.
#
#   ci history
#       Show recent CI runs for the current branch.
#
#   ci logs
#       Show logs from the latest failed CI run.
#
# This script does NOT modify source code or Git history.
#
# ============================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$ROOT_DIR"


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

WORKFLOW_NAME="${SUPPORTSENSE_CI_WORKFLOW:-SupportSense CI}"
RUN_LIMIT="${SUPPORTSENSE_CI_RUN_LIMIT:-5}"


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

error() {
    echo "ERROR: $*" >&2
    exit 1
}


require_command() {
    local command_name="$1"

    if ! command -v "$command_name" >/dev/null 2>&1; then
        error "$command_name is required but was not found."
    fi
}


current_branch() {
    local branch

    branch="$(git branch --show-current 2>/dev/null || true)"

    if [[ -z "$branch" ]]; then
        error "Unable to determine the current Git branch."
    fi

    printf '%s\n' "$branch"
}


repository() {
    local repo

    repo="$(
        gh repo view \
            --json nameWithOwner \
            --jq '.nameWithOwner' \
            2>/dev/null || true
    )"

    if [[ -z "$repo" ]]; then
        error "Unable to determine the GitHub repository."
    fi

    printf '%s\n' "$repo"
}


latest_run_id() {
    local branch="$1"
    local repo="$2"
    local run_id

    run_id="$(
        gh run list \
            --repo "$repo" \
            --workflow "$WORKFLOW_NAME" \
            --branch "$branch" \
            --limit 1 \
            --json databaseId \
            --jq '.[0].databaseId' \
            2>/dev/null || true
    )"

    if [[ -z "$run_id" ]]; then
        error "No CI run found for branch '$branch'."
    fi

    printf '%s\n' "$run_id"
}


# ------------------------------------------------------------
# Commands
# ------------------------------------------------------------

ci_status() {
    local branch="$1"
    local repo="$2"

    echo "============================================================"
    echo " SupportSense GitHub Actions"
    echo " CI STATUS"
    echo "============================================================"
    echo
    echo "Repository:"
    echo "    $repo"
    echo
    echo "Branch:"
    echo "    $branch"
    echo

    gh run list \
        --repo "$repo" \
        --workflow "$WORKFLOW_NAME" \
        --branch "$branch" \
        --limit 1
}


ci_history() {
    local branch="$1"
    local repo="$2"

    echo "============================================================"
    echo " SupportSense GitHub Actions"
    echo " CI HISTORY"
    echo "============================================================"
    echo
    echo "Repository:"
    echo "    $repo"
    echo
    echo "Branch:"
    echo "    $branch"
    echo

    gh run list \
        --repo "$repo" \
        --workflow "$WORKFLOW_NAME" \
        --branch "$branch" \
        --limit "$RUN_LIMIT"
}


ci_watch() {
    local branch="$1"
    local repo="$2"
    local run_id="$3"

    echo "============================================================"
    echo " SupportSense GitHub Actions"
    echo " CI WATCH"
    echo "============================================================"
    echo
    echo "Repository:"
    echo "    $repo"
    echo
    echo "Branch:"
    echo "    $branch"
    echo
    echo "Run ID:"
    echo "    $run_id"
    echo
    echo "Watching CI until completion..."
    echo

    gh run watch \
        "$run_id" \
        --repo "$repo" \
        --exit-status
}


ci_logs() {
    local branch="$1"
    local repo="$2"
    local run_id="$3"

    echo "============================================================"
    echo " SupportSense GitHub Actions"
    echo " CI LOGS"
    echo "============================================================"
    echo
    echo "Repository:"
    echo "    $repo"
    echo
    echo "Branch:"
    echo "    $branch"
    echo
    echo "Run ID:"
    echo "    $run_id"
    echo

    gh run view \
        "$run_id" \
        --repo "$repo" \
        --log-failed
}


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

require_command git
require_command gh

BRANCH="$(current_branch)"
REPO="$(repository)"

COMMAND="${1:-watch}"

case "$COMMAND" in

    watch|ci)
        RUN_ID="$(latest_run_id "$BRANCH" "$REPO")"
        ci_watch "$BRANCH" "$REPO" "$RUN_ID"
        ;;

    status)
        ci_status "$BRANCH" "$REPO"
        ;;

    history)
        ci_history "$BRANCH" "$REPO"
        ;;

    logs)
        RUN_ID="$(latest_run_id "$BRANCH" "$REPO")"
        ci_logs "$BRANCH" "$REPO" "$RUN_ID"
        ;;

    help|-h|--help)
        cat <<'USAGE'

SupportSense GitHub Actions CI

Usage:
    ./scripts/supportsense.sh ci [command]

Commands:

    ci
        Watch the latest CI run for the current branch.

    ci status
        Show the latest CI run status.

    ci history
        Show recent CI runs.

    ci logs
        Show failed logs from the latest CI run.

Examples:

    ./scripts/supportsense.sh ci
    ./scripts/supportsense.sh ci status
    ./scripts/supportsense.sh ci history
    ./scripts/supportsense.sh ci logs

Environment overrides:

    SUPPORTSENSE_CI_WORKFLOW
        GitHub Actions workflow name.
        Default: SupportSense CI

    SUPPORTSENSE_CI_RUN_LIMIT
        Number of historical runs to display.
        Default: 5

USAGE
        ;;

    *)
        error "Unknown CI command: $COMMAND"
        ;;
esac
