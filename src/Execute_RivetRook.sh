#!/usr/bin/env bash
# Linux/macOS launcher for RivetRook. Works from any cwd and, when started
# from a file manager (no TTY), reopens itself inside a terminal emulator.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"

if [ ! -t 0 ] && [ -z "$RIVETROOK_IN_TERMINAL" ]; then
    export RIVETROOK_IN_TERMINAL=1
    for term in x-terminal-emulator gnome-terminal ptyxis konsole xfce4-terminal kitty alacritty xterm; do
        if command -v "$term" >/dev/null 2>&1; then
            case "$term" in
                gnome-terminal|ptyxis) exec "$term" -- bash "$SCRIPT_PATH" ;;
                *) exec "$term" -e bash "$SCRIPT_PATH" ;;
            esac
        fi
    done
    echo "[X] Nenhum emulador de terminal encontrado." >&2
    exit 1
fi

cd "$SCRIPT_DIR" || exit 1

if command -v python3 >/dev/null 2>&1; then
    PY_CMD=python3
elif command -v python >/dev/null 2>&1; then
    PY_CMD=python
else
    echo
    echo " [X] Python nao foi encontrado no sistema."
    echo "     Instale o Python 3 pelo gerenciador de pacotes (ex.: sudo apt install python3)."
    echo
    read -rp "  Pressione Enter para sair..." _
    exit 1
fi

"$PY_CMD" "$SCRIPT_DIR/RivetRook.py" "$@"
STATUS=$?

# Keep the window open when launched by double-click so output stays visible.
if [ -n "$RIVETROOK_IN_TERMINAL" ]; then
    echo
    read -rp "  Pressione Enter para fechar..." _
fi
exit $STATUS
