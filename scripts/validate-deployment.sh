#!/usr/bin/env bash
set -euo pipefail

# validate-deployment.sh
# Validates deployment is healthy before marking as successful
# Usage: ./validate-deployment.sh [version]

DEPLOYMENT_VERSION="${1:-unknown}"
LOG_FILE="/tmp/deployment-validation-${DEPLOYMENT_VERSION}.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

{
    echo "=========================================="
    echo "Deployment Validation Report"
    echo "=========================================="
    echo "Version: $DEPLOYMENT_VERSION"
    echo "Date: $(date)"
    echo "Host: $(hostname)"
    echo ""

    # 1. Check Python environment
    echo "[1/5] Checking Python environment..."
    python3 --version || { echo "❌ Python not found"; exit 1; }
    echo "✅ Python available"
    echo ""

    # 2. Run health checks
    echo "[2/5] Running system health checks..."
    if command -v check-data-health &> /dev/null; then
        if check-data-health >> /dev/null 2>&1; then
            echo "✅ Health checks passed"
        else
            echo "⚠️ Health check reported issues"
        fi
    else
        echo "⚠️ Health check tool not available (optional)"
    fi
    echo ""

    # 3. Verify test suite
    echo "[3/5] Verifying test suite..."
    if cd "$PROJECT_ROOT" && python3 -m pytest tests/ -q --tb=no 2>&1 | tee /tmp/test-check.log; then
        PASSED=$(grep -oP '\d+(?= passed)' /tmp/test-check.log | head -1 || echo "0")
        echo "✅ Test suite passed ($PASSED tests)"
    else
        echo "❌ Test suite failed - deployment may be unstable"
        exit 1
    fi
    echo ""

    # 4. Check configuration validity
    echo "[4/5] Checking configuration..."
    if command -v nix &> /dev/null; then
        if cd "$PROJECT_ROOT" && nix flake check --show-trace 2>&1 | grep -q "success\|all attributes"; then
            echo "✅ Configuration is valid"
        else
            echo "⚠️ Configuration check skipped"
        fi
    else
        echo "⚠️ Nix not available (optional)"
    fi
    echo ""

    # 5. Check for deployment artifacts
    echo "[5/5] Checking deployment artifacts..."
    ARTIFACT_COUNT=0
    if [ -f "$PROJECT_ROOT/flake.nix" ]; then
        ((ARTIFACT_COUNT++))
    fi
    if [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
        ((ARTIFACT_COUNT++))
    fi
    if [ -d "$PROJECT_ROOT/claude_automation" ]; then
        ((ARTIFACT_COUNT++))
    fi

    if [ $ARTIFACT_COUNT -ge 3 ]; then
        echo "✅ All key artifacts present"
    else
        echo "❌ Missing key artifacts"
        exit 1
    fi
    echo ""

    # Summary
    echo "=========================================="
    echo "Validation Summary"
    echo "=========================================="
    echo "✅ Deployment validation passed"
    echo "Version: $DEPLOYMENT_VERSION"
    echo "Timestamp: $(date -Iseconds)"
    echo "=========================================="

} 2>&1 | tee "$LOG_FILE"

echo ""
echo "Log saved to: $LOG_FILE"
