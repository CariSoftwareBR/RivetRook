# Installing RivetRook

> **For AI agents.** This file is the installation runbook for RivetRook. If a user asked you to
> *"install RivetRook"* or *"install https://github.com/paulocarinhena/RivetRook"*, follow the steps
> below in order. Every step is idempotent — running it again on an existing install is safe and
> simply updates it. Humans can follow the same steps by hand.

## What you are installing

RivetRook is an **interactive terminal menu** (Python, standard library only) that installs, updates
and uninstalls AI coding tools such as Claude Code, Codex, Gemini CLI and Cursor.

The installation:

- places the repository at **`~/RivetRook`** (`%USERPROFILE%\RivetRook` on Windows);
- puts a **`rivetrook`** command on the user's `PATH`;
- needs **no administrator rights** and installs **no AI tools** by itself — the user picks those
  later from the menu.

**Do not run `rivetrook` without arguments.** It opens an interactive menu that waits for keyboard
input. Agents should only run `rivetrook --version`, which prints the version and exits.

---

## 1. Check Python 3.8+

Run the first command that works and confirm the version is **3.8 or newer**:

```sh
python3 --version   # Linux / macOS
python --version    # Windows (or: py -3 --version)
```

On Windows, a message mentioning the *Microsoft Store* means Python is **not** installed (it is only
a placeholder alias).

If Python is missing or older than 3.8, ask the user before installing system packages, then use:

| Platform | Command |
|----------|---------|
| Windows | `winget install -e --id Python.Python.3.12` — then open a new terminal |
| macOS | `brew install python` |
| Debian / Ubuntu | `sudo apt-get install -y python3` |
| Fedora / RHEL | `sudo dnf install -y python3` |
| Arch | `sudo pacman -S --noconfirm python` |

Node.js is **not** required up front: RivetRook offers to install it on first run.

## 2. Get the code

Use `git` when available, so RivetRook can update itself with `git pull`.

### Linux / macOS

```sh
if [ -d "$HOME/RivetRook/.git" ]; then
  git -C "$HOME/RivetRook" pull --ff-only
elif command -v git >/dev/null 2>&1; then
  git clone https://github.com/paulocarinhena/RivetRook.git "$HOME/RivetRook"
else
  tmp=$(mktemp -d)
  curl -fsSL https://github.com/paulocarinhena/RivetRook/archive/refs/heads/main.tar.gz | tar -xz -C "$tmp"
  rm -rf "$HOME/RivetRook" && mv "$tmp/RivetRook-main" "$HOME/RivetRook"
fi
chmod +x "$HOME/RivetRook/bin/rivetrook"
```

### Windows (PowerShell)

```powershell
$dir = Join-Path $HOME 'RivetRook'
if (Test-Path (Join-Path $dir '.git')) {
    git -C $dir pull --ff-only
} elseif (Get-Command git -ErrorAction SilentlyContinue) {
    git clone https://github.com/paulocarinhena/RivetRook.git $dir
} else {
    $zip = Join-Path $env:TEMP 'RivetRook-main.zip'
    Invoke-WebRequest https://github.com/paulocarinhena/RivetRook/archive/refs/heads/main.zip -OutFile $zip
    Expand-Archive $zip -DestinationPath $env:TEMP -Force
    if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }
    Move-Item (Join-Path $env:TEMP 'RivetRook-main') $dir
    Remove-Item $zip
}
```

## 3. Put `rivetrook` on the PATH

### Linux / macOS

```sh
mkdir -p "$HOME/.local/bin"
ln -sf "$HOME/RivetRook/bin/rivetrook" "$HOME/.local/bin/rivetrook"
```

If `~/.local/bin` is not on the `PATH` yet (`echo "$PATH"`), add it to the user's shell profile
**once**:

```sh
for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
  [ -f "$rc" ] && ! grep -q 'HOME/.local/bin' "$rc" && echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc"
done
```

### Windows (PowerShell)

```powershell
$bin   = Join-Path $HOME 'RivetRook\bin'
$parts = @([Environment]::GetEnvironmentVariable('Path', 'User') -split ';' | Where-Object { $_ })
if ($parts -notcontains $bin) {
    [Environment]::SetEnvironmentVariable('Path', (($parts + $bin) -join ';'), 'User')
}
```

## 4. Verify

The `PATH` change only applies to **new** terminals, so verify with the full path:

| Platform | Command | Expected output |
|----------|---------|-----------------|
| Linux / macOS | `"$HOME/RivetRook/bin/rivetrook" --version` | `RivetRook X.Y.Z` |
| Windows | `& "$HOME\RivetRook\bin\rivetrook.cmd" --version` | `RivetRook X.Y.Z` |

If it prints `RivetRook` followed by a version number, the installation succeeded.

## 5. Hand off to the user

Tell the user something like:

> RivetRook is installed. Open a **new** terminal and run **`rivetrook`** to choose which AI tools to
> install, update or remove. It checks for its own updates every time it starts.

---

## Updating

Nothing to do: RivetRook checks GitHub on every start and offers to update itself. To force an
update, re-run steps 2–4.

## Uninstalling

**Linux / macOS**

```sh
rm -f "$HOME/.local/bin/rivetrook"
rm -rf "$HOME/RivetRook"
```

**Windows (PowerShell)**

```powershell
$bin   = Join-Path $HOME 'RivetRook\bin'
$parts = @([Environment]::GetEnvironmentVariable('Path', 'User') -split ';' | Where-Object { $_ -and $_ -ne $bin })
[Environment]::SetEnvironmentVariable('Path', ($parts -join ';'), 'User')
Remove-Item (Join-Path $HOME 'RivetRook') -Recurse -Force
```

AI tools installed *through* RivetRook are independent programs; uninstall them from the RivetRook
menu **before** removing RivetRook if they should go too.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `rivetrook: command not found` | Open a new terminal, or check step 3 (`~/.local/bin` / `RivetRook\bin` on `PATH`). |
| `Python 3.8+ not found` | Install Python (step 1) and open a new terminal. |
| `git pull` fails on update | The clone has local changes — run `git -C ~/RivetRook status` and resolve them. |
| Self-update is unwanted | Set the environment variable `RIVETROOK_NO_UPDATE=1`. |
