#!/usr/bin/env bash

# ============================================================
# SupportSense Development Environment
# GIT / GITHUB SAFETY SCRIPT
# ============================================================
#
# Provides a controlled interface to Git operations.
#
# Normal Git commands are passed through.
#
# Commit and push operations receive additional safety checks
# before the underlying Git command is executed.
#
# Safety checks are intentionally conservative:
#   - repository validation
#   - Git working-tree inspection
#   - sensitive filename detection
#   - high-confidence secret pattern detection
#   - whitespace/error checking
#
# This script NEVER prints secret values intentionally.
#
# ============================================================

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "$ROOT_DIR"

error() {
    echo
    echo "ERROR: $*" >&2
    exit 1
}

require_command() {
    local command_name="$1"

    if ! command -v "$command_name" >/dev/null 2>&1; then
        error "$command_name is required but was not found."
    fi
}

require_git_repository() {
    git rev-parse --show-toplevel >/dev/null 2>&1 ||
        error "This directory is not inside a Git repository."
}

show_status() {
    echo "===== GIT STATUS ====="
    git status --short --branch
    echo
}

check_sensitive_filenames() {
    echo "===== SENSITIVE FILENAME CHECK ====="

    local found=0

    while IFS= read -r file; do
        case "$file" in
            .env|.env.*|*.pem|*.key|*.p12|*.pfx|*.jks|\
            credentials.json|service-account.json|\
            secrets.json|secret.json)
                echo "BLOCKED: sensitive filename detected: $file"
                found=1
                ;;
        esac
    done < <(
        git ls-files --cached --others --exclude-standard
    )

    if [[ "$found" -ne 0 ]]; then
        error "Sensitive files detected. Commit/push blocked."
    fi

    echo "PASS: no sensitive filenames detected."
    echo
}

check_secret_patterns() {
    echo "===== SECRET CONTENT CHECK ====="

    local diff_file
    diff_file="$(mktemp)"

    # Scan exactly what is staged for the operation.
    # This is the content that a commit would actually contain.
    git diff --cached --binary > "$diff_file" || true

    if [[ ! -s "$diff_file" ]]; then
        rm -f "$diff_file"
        echo "No staged diff detected."
        echo "PASS: no candidate secret content detected."
        echo
        return
    fi

    local patterns=(
        'AKIA[0-9A-Z]{16}'
        'ASIA[0-9A-Z]{16}'
        'gh[pousr]_[A-Za-z0-9_]{20,}'
        'github_pat_[A-Za-z0-9_]{20,}'
        '-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'
        'Authorization:[[:space:]]*Bearer[[:space:]]+[A-Za-z0-9._~+/=-]{20,}'
        'api[_-]?key[[:space:]]*=[[:space:]]*["'\''][^"'\'']{12,}["'\'']'
        'secret[[:space:]]*=[[:space:]]*["'\''][^"'\'']{12,}["'\'']'
        'password[[:space:]]*=[[:space:]]*["'\''][^"'\'']{8,}["'\'']'
    )

    local detected=0

    for pattern in "${patterns[@]}"; do
        if grep -Eqi -- "$pattern" "$diff_file"; then
            echo "BLOCKED: high-confidence secret pattern detected."
            detected=1
        fi
    done

    rm -f "$diff_file"

    if [[ "$detected" -ne 0 ]]; then
        echo
        echo "The actual matching secret value is intentionally not displayed."
        error "Potential secret detected. Commit/push blocked."
    fi

    echo "PASS: no high-confidence secret patterns detected."
    echo
}

check_git_diff() {
    echo "===== GIT DIFF CHECK ====="

    if ! git diff --check; then
        error "Git whitespace/error check failed."
    fi

    echo "PASS: git diff --check"
    echo
}

preflight() {
    local operation="$1"

    echo
    echo "============================================================"
    echo " SupportSense Git Safety Check"
    echo " OPERATION: $operation"
    echo "============================================================"
    echo

    require_command git
    require_git_repository

    echo "Repository:"
    git rev-parse --show-toplevel

    echo
    echo "Branch:"
    git branch --show-current

    echo

    show_status
    check_sensitive_filenames
    check_secret_patterns
    check_git_diff

    echo "============================================================"
    echo " SAFETY CHECK PASSED"
    echo "============================================================"
    echo
}

git_commit() {
    if [[ "$#" -eq 0 ]]; then
        error "Usage: ./scripts/supportsense.sh commit <git commit arguments>"
    fi

    preflight "git commit $*"

    echo "Executing:"
    printf '  git commit'
    printf ' %q' "$@"
    echo
    echo

    git commit "$@"
}

git_push() {
    if [[ "$#" -eq 0 ]]; then
        error "Usage: ./scripts/supportsense.sh push <git push arguments>"
    fi

    preflight "git push $*"

    echo "Executing:"
    printf '  git push'
    printf ' %q' "$@"
    echo
    echo

    git push "$@"
}

git_passthrough() {
    if [[ "$#" -eq 0 ]]; then
        error "Usage: ./scripts/supportsense.sh git <git arguments>"
    fi

    git "$@"
}

COMMAND="${1:-help}"
shift || true

case "$COMMAND" in

    commit)
        git_commit "$@"
        ;;

    push)
        git_push "$@"
        ;;

    help|-h|--help)
        cat <<'USAGE'
SupportSense Git Helper

Usage:
    ./scripts/supportsense.sh git <git arguments>
    ./scripts/supportsense.sh commit <git commit arguments>
    ./scripts/supportsense.sh push <git push arguments>

Examples:
    ./scripts/supportsense.sh git status
    ./scripts/supportsense.sh git diff --check
    ./scripts/supportsense.sh git log -5 --oneline
    ./scripts/supportsense.sh git show --stat HEAD
    ./scripts/supportsense.sh git remote -v

    ./scripts/supportsense.sh commit -m "Commit message"
    ./scripts/supportsense.sh push origin feature/sprint-7-observability

Safety:
    commit and push operations automatically run the
    SupportSense Git safety checks before Git executes.

    All other Git commands are passed through unchanged.
USAGE
        ;;

    *)
        git_passthrough "$COMMAND" "$@"
        ;;

esac
