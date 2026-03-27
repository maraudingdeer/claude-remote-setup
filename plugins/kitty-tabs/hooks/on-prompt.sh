#!/bin/bash
# When user submits a prompt, clear the done indicator
[ -z "$KITTY_LISTEN_ON" ] && exit 0

DIR_NAME=$(basename "$PWD")
kitty @ --to "$KITTY_LISTEN_ON" set-tab-title "$DIR_NAME" 2>/dev/null
exit 0
