#!/bin/sh
# RivetRook one-line installer for Linux and macOS:
#
#   curl -fsSL https://raw.githubusercontent.com/CariSoftwareBR/RivetRook/main/install.sh | sh
#
# Installs everything RivetRook needs (Python 3.8+ when missing, asking for the
# sudo password if required), puts `rivetrook` on the PATH and leaves it ready to
# run in the same terminal. Idempotent: running it again updates an existing
# install. Mirrors INSTALLATION.md. Everything lives in a function called on the
# last line, so a download cut short never runs a partial script.

set -u

REPO_URL="https://github.com/CariSoftwareBR/RivetRook.git"
TARBALL_URL="https://github.com/CariSoftwareBR/RivetRook/archive/refs/heads/main.tar.gz"

say()  { printf '  %s\n' "$*"; }
fail() { printf '\n  [X] %s\n\n' "$*" >&2; exit 1; }

as_root() {
    if [ "$(id -u)" = 0 ]; then
        "$@"
    elif command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    elif command -v doas >/dev/null 2>&1; then
        doas "$@"
    else
        return 1
    fi
}

find_python() {
    for candidate in python3 python; do
        command -v "$candidate" >/dev/null 2>&1 || continue
        # macOS ships a /usr/bin/python3 stub that pops up the Command Line
        # Tools dialog when run before they are installed: never probe it then.
        if [ "$(uname -s)" = Darwin ] && [ "$(command -v "$candidate")" = "/usr/bin/$candidate" ] \
            && ! xcode-select -p >/dev/null 2>&1; then
            continue
        fi
        if "$candidate" -c "import sys; sys.exit(sys.version_info < (3, 8))" >/dev/null 2>&1; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

download() {
    # $1 = URL, written to stdout.
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$1"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- "$1"
    else
        return 1
    fi
}

get_code() {
    dir=$1
    if [ -d "$dir/.git" ] && command -v git >/dev/null 2>&1; then
        say "Updating $dir (git pull)..."
        git -C "$dir" pull --ff-only --quiet \
            || fail "git pull failed in $dir. Check 'git -C \"$dir\" status' and try again."
    elif command -v git >/dev/null 2>&1 && [ ! -e "$dir" ]; then
        say "Cloning RivetRook into $dir..."
        git clone --quiet "$REPO_URL" "$dir" || fail "git clone failed."
    else
        # No git (or a previous non-git copy): plain download. RivetRook then
        # updates itself by downloading its own files.
        say "Downloading RivetRook into $dir..."
        tmp=$(mktemp -d) || fail "Could not create a temporary directory."
        if ! download "$TARBALL_URL" | tar -xz -C "$tmp"; then
            rm -rf "$tmp"
            fail "Download failed. Install curl or wget (or git) and try again."
        fi
        [ -f "$tmp/RivetRook-main/src/RivetRook.py" ] || { rm -rf "$tmp"; fail "Downloaded archive is incomplete."; }
        rm -rf "$dir" && mv "$tmp/RivetRook-main" "$dir" || fail "Could not move files into $dir."
        rm -rf "$tmp"
    fi
    chmod +x "$dir/bin/rivetrook" "$dir/src/RivetRook.py" 2>/dev/null
}

ensure_path() {
    bin_dir=$1
    case ":$PATH:" in
        *":$bin_dir:"*) return 0 ;;
    esac
    line='export PATH="$HOME/.local/bin:$PATH"'
    added=
    for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
        if [ -f "$rc" ]; then
            grep -q 'HOME/.local/bin' "$rc" || printf '\n%s\n' "$line" >> "$rc"
            added=1
        fi
    done
    if [ -z "$added" ]; then
        # No rc file yet: macOS defaults to zsh, most Linux shells read .profile.
        case "${SHELL:-}" in
            */zsh) rc="$HOME/.zshrc" ;;
            *) rc="$HOME/.profile" ;;
        esac
        if [ ! -f "$rc" ] || ! grep -q 'HOME/.local/bin' "$rc"; then
            printf '\n%s\n' "$line" >> "$rc"
        fi
    fi
}

install_macos_clt() {
    # Headless Command Line Tools install (same approach as Homebrew's installer):
    # provides python3 (and git) without the GUI dialog.
    flag=/tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress
    as_root touch "$flag" || return 1
    label=$(softwareupdate -l 2>/dev/null | grep -B 1 -E 'Command Line Tools' \
        | awk -F'*' '/^ *\*/ {print $2}' | sed -e 's/^ *Label: //' -e 's/^ *//' \
        | sort -V | tail -n1)
    status=1
    if [ -n "$label" ]; then
        as_root softwareupdate -i "$label" </dev/null && status=0
    fi
    as_root rm -f "$flag"
    return $status
}

install_python() {
    say "Python 3.8+ not found: installing it (your password may be requested)..."
    if [ "$(uname -s)" = Darwin ]; then
        if command -v brew >/dev/null 2>&1; then
            brew install python </dev/null
        else
            install_macos_clt
        fi
    elif command -v apt-get >/dev/null 2>&1; then
        as_root env DEBIAN_FRONTEND=noninteractive apt-get update -qq </dev/null \
            && as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 </dev/null
    elif command -v dnf >/dev/null 2>&1; then
        as_root dnf install -y python3 </dev/null
    elif command -v yum >/dev/null 2>&1; then
        as_root yum install -y python3 </dev/null
    elif command -v pacman >/dev/null 2>&1; then
        as_root pacman -Sy --noconfirm --needed python </dev/null
    elif command -v zypper >/dev/null 2>&1; then
        as_root zypper --non-interactive install python3 </dev/null
    elif command -v apk >/dev/null 2>&1; then
        as_root apk add --no-cache python3 </dev/null
    else
        return 1
    fi
}

link_alias() {
    # Short `rivet` command next to `rivetrook`. Never replaces an existing
    # file nor shadows another `rivet` program already on the PATH.
    # $1 = launcher, $2 = directory, $3 = optional "as_root".
    alias_path="$2/rivet"
    [ -e "$alias_path" ] || [ -L "$alias_path" ] && return 0
    other=$(command -v rivet 2>/dev/null) || other=
    [ -n "$other" ] && return 0
    ${3:-} ln -s "$1" "$alias_path" </dev/null 2>/dev/null || true
}

link_command() {
    # Always link into ~/.local/bin (and keep it on PATH for future terminals).
    # When it is not on the PATH of the current shell yet, also link into
    # /usr/local/bin so `rivetrook` works right away, without a new terminal.
    target="$1/bin/rivetrook"
    bin_dir="$HOME/.local/bin"
    mkdir -p "$bin_dir" || fail "Could not create $bin_dir."
    ln -sf "$target" "$bin_dir/rivetrook" || fail "Could not link $bin_dir/rivetrook."
    link_alias "$target" "$bin_dir"
    ensure_path "$bin_dir"
    READY_NOW=
    case ":$PATH:" in
        *":$bin_dir:"*) READY_NOW=1; return 0 ;;
    esac
    case ":$PATH:" in
        *":/usr/local/bin:"*)
            if [ -w /usr/local/bin ] || { [ ! -e /usr/local/bin ] && [ -w /usr/local ]; }; then
                mkdir -p /usr/local/bin && ln -sf "$target" /usr/local/bin/rivetrook && READY_NOW=1 \
                    && link_alias "$target" /usr/local/bin
            else
                say "Linking /usr/local/bin/rivetrook (your password may be requested)..."
                as_root mkdir -p /usr/local/bin </dev/null \
                    && as_root ln -sf "$target" /usr/local/bin/rivetrook </dev/null && READY_NOW=1 \
                    && link_alias "$target" /usr/local/bin as_root
            fi
            ;;
    esac
    return 0
}

main() {
    dir="$HOME/RivetRook"

    printf '\n  RivetRook installer\n\n'

    if ! py=$(find_python); then
        install_python
        hash -r 2>/dev/null
        py=$(find_python) || fail "Could not install Python 3.8+ automatically.
      Install it with your package manager (e.g. sudo apt-get install -y python3)
      and run this installer again."
        say "[OK] Python installed."
    fi

    get_code "$dir"

    link_command "$dir"

    version=$("$dir/bin/rivetrook" --version 2>/dev/null) \
        || fail "Installed, but '$dir/bin/rivetrook --version' failed (Python: $py)."

    printf '\n'
    say "[OK] $version installed in $dir"
    cmd=rivetrook
    [ -L "$HOME/.local/bin/rivet" ] && cmd="rivetrook (or: rivet)"
    if [ -n "$READY_NOW" ]; then
        say "Run: $cmd"
    else
        say "Open a NEW terminal and run: $cmd"
    fi
    say "RivetRook checks for updates every time it starts."
    printf '\n'
}

main "$@"
