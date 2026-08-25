#!/usr/bin/env bash

# ============================================================
# SupportSense Development Environment
# AIRFLOW DEVELOPER ACCESS
# ============================================================
#
# Usage:
#   ./scripts/supportsense.sh airflow credentials
#
# Displays the current local SupportSense Airflow login
# credentials using Airflow's generated SimpleAuthManager
# password file.
#
# IMPORTANT:
#   - Password is retrieved dynamically from the running
#     Airflow container.
#   - Credentials are never stored in this repository.
#   - This command is intended for local development only.
#
# ============================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
source "$ROOT_DIR/scripts/lib/dev-config.sh"

AIRFLOW_DIR="$ROOT_DIR/airflow"
AIRFLOW_SERVICE="supportsense-airflow-apiserver"
AIRFLOW_USERNAME="admin"
AIRFLOW_PASSWORD_FILE='$AIRFLOW_HOME/simple_auth_manager_passwords.json.generated'

case "${1:-credentials}" in

    credentials)

        echo "============================================================"
        echo " SupportSense Airflow Credentials"
        echo "============================================================"
        echo
        echo "URL:"
        echo "    $AIRFLOW_URL"
        echo
        echo "Username:"
        echo "    $AIRFLOW_USERNAME"
        echo
        echo "Password:"
        echo

        if [[ ! -f "$AIRFLOW_DIR/docker-compose.yaml" ]]; then
            echo "ERROR: Airflow Compose configuration not found:"
            echo "       $AIRFLOW_DIR/docker-compose.yaml"
            exit 1
        fi

        cd "$AIRFLOW_DIR"

        if ! docker compose ps --status running \
            --services 2>/dev/null |
            grep -qx "$AIRFLOW_SERVICE"; then

            echo "ERROR: SupportSense Airflow API server is not running."
            echo
            echo "Start the development environment first:"
            echo
            echo "    ./scripts/supportsense.sh start"
            exit 1
        fi

        PASSWORD="$(
            docker compose exec -T "$AIRFLOW_SERVICE" \
                sh -lc "cat $AIRFLOW_PASSWORD_FILE" |
            python3 -c '
import json
import sys

data = json.load(sys.stdin)

password = data.get("admin")

if not password:
    raise SystemExit(
        "ERROR: Generated Airflow password for admin was not found."
    )

print(password)
'
        )"

        echo "    $PASSWORD"
        echo
        echo "Password source:"
        echo "    \$AIRFLOW_HOME/simple_auth_manager_passwords.json.generated"
        echo
        echo "Development login:"
        echo "    Open:     $AIRFLOW_URL"
        echo "    Username: $AIRFLOW_USERNAME"
        echo "    Password: <value shown above>"
        echo
        echo "WARNING: Development credentials only."
        ;;

    *)
        echo "Usage:"
        echo "    ./scripts/supportsense.sh airflow credentials"
        exit 1
        ;;

esac
