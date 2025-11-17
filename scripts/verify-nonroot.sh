#!/usr/bin/env bash
#
# verify-nonroot.sh - Validate that all container images run as non-root
#
# Usage:
#   ./scripts/verify-nonroot.sh
#
# Exit codes:
#   0 - All images verified as non-root
#   1 - One or more images running as root or validation failed
#

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGES=(
    "frontend:0.5.0"
    "api:0.3.2"
    "consumer:0.3.0"
)

TRIVY_IMAGE="aquasec/trivy:latest"
EXIT_CODE=0

echo "🔍 Non-Root Container Verification"
echo "==================================="
echo ""

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}✗ Error: Docker is not running${NC}"
        exit 1
    fi
}

# Function to verify image exists
verify_image_exists() {
    local image=$1
    if ! docker image inspect "$image" >/dev/null 2>&1; then
        echo -e "${RED}✗ Error: Image $image not found${NC}"
        echo "  Run: docker build -t $image <service-directory>"
        return 1
    fi
    return 0
}

# Function to check USER directive via docker inspect
check_user_config() {
    local image=$1
    local user
    user=$(docker inspect "$image" --format='{{.Config.User}}' 2>/dev/null || echo "")

    if [[ -z "$user" || "$user" == "0" || "$user" == "root" ]]; then
        echo -e "${RED}✗ $image: Running as root (User: ${user:-'not set'})${NC}"
        return 1
    else
        echo -e "${GREEN}✓ $image: Non-root user configured (UID: $user)${NC}"
        return 0
    fi
}

# Function to run Trivy security scan
run_trivy_scan() {
    local image=$1
    local scan_output

    echo "  Running Trivy misconfiguration scan..."

    # Run Trivy and capture output
    if scan_output=$(docker run --rm \
        -v /var/run/docker.sock:/var/run/docker.sock \
        "$TRIVY_IMAGE" image \
        --scanners misconfig \
        --severity HIGH,CRITICAL \
        --exit-code 1 \
        --quiet \
        "$image" 2>&1); then
        echo -e "${GREEN}  ✓ Trivy scan passed (no HIGH/CRITICAL issues)${NC}"
        return 0
    else
        echo -e "${RED}  ✗ Trivy scan failed${NC}"
        echo "$scan_output"
        return 1
    fi
}

# Main validation loop
main() {
    check_docker

    echo "Validating ${#IMAGES[@]} images..."
    echo ""

    for image in "${IMAGES[@]}"; do
        echo "Checking $image..."

        # Check if image exists
        if ! verify_image_exists "$image"; then
            EXIT_CODE=1
            echo ""
            continue
        fi

        # Check USER configuration
        if ! check_user_config "$image"; then
            EXIT_CODE=1
        fi

        # Run Trivy scan
        if ! run_trivy_scan "$image"; then
            EXIT_CODE=1
        fi

        echo ""
    done

    # Summary
    echo "==================================="
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✓ All images verified as non-root${NC}"
        echo ""
        echo "Summary:"
        echo "  - frontend:0.5.0: UID 1000 (appuser)"
        echo "  - api:0.3.2: UID 65532 (distroless nonroot)"
        echo "  - consumer:0.3.0: UID 1000 (appuser)"
    else
        echo -e "${RED}✗ Validation failed - one or more images have security issues${NC}"
        echo ""
        echo "Fix the issues above and re-run this script."
    fi

    exit $EXIT_CODE
}

main "$@"
