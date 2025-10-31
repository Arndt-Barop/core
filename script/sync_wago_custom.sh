#!/bin/bash
# Sync WAGO Energy Meter integration to custom component repository
# Usage: ./script/sync_wago_custom.sh [commit-message]

set -e

# Configuration
INTEGRATION_PATH="homeassistant/components/wago_energymeter"
TESTS_PATH="tests/components/wago_energymeter"
CUSTOM_REPO_URL="https://git.uncletombbg.duckdns.org/Pinky_und_Brain/HomeAssistant"
CUSTOM_REPO_BRANCH="main"
TMP_DIR="/tmp/wago-custom-sync-$$"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 WAGO Energy Meter Custom Integration Sync${NC}"
echo "================================================"

# Check if we're in the correct directory
if [ ! -d "$INTEGRATION_PATH" ]; then
    echo -e "${RED}❌ Error: $INTEGRATION_PATH not found${NC}"
    echo "Please run this script from the Home Assistant core repository root"
    exit 1
fi

if [ ! -d "$TESTS_PATH" ]; then
    echo -e "${YELLOW}⚠️  Warning: $TESTS_PATH not found${NC}"
    echo "Tests will not be synced"
    SYNC_TESTS=false
else
    SYNC_TESTS=true
fi

# No git check - we sync directly from working directory
echo -e "${GREEN}📂 Syncing from working directory (no core commit needed)${NC}"

# Get commit message
COMMIT_MSG="${1:-Sync from core development $(date +%Y-%m-%d)}"

echo -e "${GREEN}📦 Preparing sync...${NC}"

# Create temporary directory
mkdir -p "$TMP_DIR"
trap "rm -rf $TMP_DIR" EXIT

# Clone the custom repo
echo -e "${GREEN}📥 Cloning custom integration repository...${NC}"
git clone --depth 1 "$CUSTOM_REPO_URL" "$TMP_DIR"
cd "$TMP_DIR"

# Determine the target directory structure
# Check if it uses custom_components or direct structure
if [ -d "custom_components" ]; then
    TARGET_DIR="custom_components/wago_energymeter"
elif [ -f "manifest.json" ]; then
    # Direct structure (root is the integration)
    TARGET_DIR="."
else
    # Create custom_components structure
    mkdir -p "custom_components"
    TARGET_DIR="custom_components/wago_energymeter"
fi

echo -e "${GREEN}🎯 Target directory: $TARGET_DIR${NC}"

# Create target directory if needed
mkdir -p "$TARGET_DIR"

# Copy files from source
echo -e "${GREEN}📋 Copying integration files...${NC}"
rsync -av --delete \
    --exclude='.gitignore' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='Datasheets' \
    --exclude='*.code-workspace' \
    --exclude='DOCUMENTATION.md' \
    --exclude='translations' \
    "/workspaces/core/$INTEGRATION_PATH/" "$TARGET_DIR/"

# Copy tests if they exist
if [ "$SYNC_TESTS" = true ]; then
    echo -e "${GREEN}🧪 Copying test files...${NC}"
    TESTS_TARGET="tests"
    mkdir -p "$TESTS_TARGET"
    rsync -av --delete \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.pytest_cache' \
        "/workspaces/core/$TESTS_PATH/" "$TESTS_TARGET/"
fi

# Copy README to root (as main documentation)
if [ -f "/workspaces/core/script/README_CUSTOM.md" ]; then
    echo -e "${GREEN}📄 Copying README documentation...${NC}"
    cp "/workspaces/core/script/README_CUSTOM.md" "README.md"
fi

# Check if there are changes
if git diff --quiet; then
    echo -e "${YELLOW}ℹ️  No changes detected - repository is up to date${NC}"
    exit 0
fi

# Show changes
echo -e "${GREEN}📝 Changes detected:${NC}"
git status --short

# Commit and push
echo -e "${GREEN}💾 Committing changes...${NC}"
git add .
git commit -m "$COMMIT_MSG"

echo -e "${GREEN}⬆️  Pushing to remote...${NC}"
git push origin "$CUSTOM_REPO_BRANCH"

echo -e "${GREEN}✅ Successfully synced WAGO Energy Meter integration!${NC}"
echo -e "${GREEN}   Commit message: $COMMIT_MSG${NC}"
