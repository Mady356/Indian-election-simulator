#!/usr/bin/env bash
# Install macOS LaunchAgent to start the platform at login (optional).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_DEST="$HOME/Library/LaunchAgents/com.election-intelligence.platform.plist"
PLIST_SRC="$ROOT/scripts/com.election-intelligence.platform.plist.template"

mkdir -p "$ROOT/logs"
mkdir -p "$HOME/Library/LaunchAgents"

sed "s|REPO_ROOT|$ROOT|g" "$PLIST_SRC" > "$PLIST_DEST"

launchctl bootout "gui/$(id -u)/com.election-intelligence.platform" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DEST"

echo "Installed LaunchAgent: $PLIST_DEST"
echo "The platform will start automatically when you log in."
echo ""
echo "  Start now:  launchctl kickstart -k gui/$(id -u)/com.election-intelligence.platform"
echo "  Uninstall:  launchctl bootout gui/$(id -u)/com.election-intelligence.platform"
echo "              rm $PLIST_DEST"
