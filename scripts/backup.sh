bash
#!/usr/bin/env bash

set -Eeuo pipefail

# Kali - Universal MongoDB Backup Automation

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" "$*"
}

error() {
    log "ERROR: $*" >&2
    exit 1
}

validate_config() {
    local required_vars=(
        PROJECT_NAME
        MONGODB_URI
        BACKUP_ROOT
        RETENTION_DAYS
        BACKUP_INTERVAL_HOURS
    )

    local var

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Required environment variable is missing: ${var}"
        fi
    done

    if [[ ! "$RETENTION_DAYS" =~ ^[1-9][0-9]*$ ]]; then
        error "RETENTION_DAYS must be a positive integer."
    fi

    if [[ ! "$BACKUP_INTERVAL_HOURS" =~ ^[1-9][0-9]*$ ]]; then
        error "BACKUP_INTERVAL_HOURS must be a positive integer."
    fi
}

main() {
    log "Kali MongoDB Backup Automation starting."

    validate_config

    log "Configuration validation successful."
    log "Project: ${PROJECT_NAME}"
    log "Local backup directory: ${BACKUP_ROOT}"
    log "Local retention: ${RETENTION_DAYS} days"
    log "Configured backup interval: ${BACKUP_INTERVAL_HOURS} hours"

    log "Configuration validated. Backup implementation is the next step."
}

main "$@"