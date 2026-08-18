#!/usr/bin/env bash

# ============================================================
# SupportSense Development Environment Controller
# ============================================================
#
# MASTER SCRIPT
#
# This is the primary operational entry point for the
# SupportSense DEVELOPMENT environment.
#
# Commands:
#
#   start
#       Start the complete local development environment.
#
#       This currently includes:
#         - MLflow server
#         - SupportSense Runner API
#         - Airflow Docker Compose stack
#
#   stop
#       Stop the local development services started by
#       SupportSense.
#
#   restart
#       Stop and then start the development environment.
#
#   status
#       Show the status and health of:
#         - MLflow
#         - Runner API
#         - Airflow
#         - PostgreSQL
#         - DVC
#
#   validate
#       Validate the development environment:
#         - Python/dependencies
#         - pip check
#         - DVC status
#         - service health
#         - automated tests
#
#   help
#       Display this command reference.
#
# IMPORTANT:
#
#   This script manages DEVELOPMENT only.
#
#   Development:
#       Current Windows/WSL laptop
#
#   Staging:
#       MacBook + Kubernetes
#
#   Production:
#       AWS
#
# The internal implementation scripts are kept under:
#
#       scripts/lib/
#
# They are intentionally separated from this master script
# so that future sprints can extend individual capabilities
# without making this file unnecessarily large.
#
# Future sprint additions may include:
#   - Prometheus
#   - Grafana
#   - Feature Store
#   - DL services
#   - LLM/RAG services
#   - Agent services
#   - additional model-serving components
#
# ============================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LIB_DIR="$ROOT_DIR/scripts/lib"

usage() {
    cat <<'USAGE'

SupportSense Development Environment

Usage:
    ./scripts/supportsense.sh <command>

Commands:

    start
        Start the complete local development environment.

    stop
        Stop the local development environment.

    restart
        Stop and start the development environment.

    status
        Show service status and health information.

    validate
        Validate dependencies, DVC, services and tests.

    help
        Show this help message.

Examples:

    ./scripts/supportsense.sh start
    ./scripts/supportsense.sh status
    ./scripts/supportsense.sh validate
    ./scripts/supportsense.sh restart
    ./scripts/supportsense.sh stop

Environment model:

    Development  ->  Current WSL laptop
    Staging      ->  MacBook + Kubernetes
    Production   ->  AWS

USAGE
}

case "${1:-help}" in
    start)
        exec "$LIB_DIR/start-dev.sh"
        ;;

    stop)
        exec "$LIB_DIR/stop-dev.sh"
        ;;

    restart)
        "$LIB_DIR/stop-dev.sh"
        echo
        exec "$LIB_DIR/start-dev.sh"
        ;;

    status)
        exec "$LIB_DIR/status-dev.sh"
        ;;

    validate)
        exec "$LIB_DIR/validate-dev.sh"
        ;;

    help|-h|--help)
        usage
        ;;

    *)
        echo "ERROR: Unknown command: $1"
        echo
        usage
        exit 1
        ;;
esac
