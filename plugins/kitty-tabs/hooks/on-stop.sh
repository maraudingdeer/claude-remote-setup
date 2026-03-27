#!/bin/bash
# When Claude stops (done or waiting for approval), mark tab green
[ -z "$KITTY_LISTEN_ON" ] && exit 0

DIR_NAME=$(basename "$PWD")
kitty @ --to "$KITTY_LISTEN_ON" set-tab-title "✅ $DIR_NAME" 2>/dev/null

# macOS notification with sound
osascript -e "display notification \"Done in $DIR_NAME\" with title \"Claude Code\" sound name \"Glass\"" 2>/dev/null &
exit 0
