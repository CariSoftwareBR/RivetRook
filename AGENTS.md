# AGENTS

## Scope and entrypoint
- This repo is a single interactive Python CLI app; runtime logic is in `src/RivetRook.py`, data/config in `src/config.json`.
- Default startup reads `src/config.json`; you can pass an alternate config path as argv[1] (`python src/RivetRook.py path/to/config.json`).

## Run and verify
- Main local run: `python src/RivetRook.py` (or `python3 src/RivetRook.py` on Linux/macOS).
- Windows helper launcher: `src/Execute_RivetRook.bat` (it can install Python and PowerShell 7, then starts `RivetRook.py` in `pwsh`).
- There is no test/lint/typecheck config or CI in this repo; validation is manual CLI smoke testing.

## Config contract (high impact)
- Tool definitions live in `config.json` under `tools` and `ides`; menu order follows JSON key order.
- `resolve_command()` only resolves `all`, `windows`, `macos`, `linux`, and Linux family keys (e.g. `debian`/`fedora`/`arch`/`default`). Keys like `all_alt`/`linux_alt` are ignored by runtime.
- `run` is required for install detection. Version detection uses `version_cmd`/`version_regex` when present; otherwise probes `--version`, `-v`, `version`.
- Latest-version lookup (the "↑ update available" marker) is inferred from `npm`/`bun`/`brew` install commands; for other installers add a `latest` block with one of `npm`, `pypi`, `brew_cask`, `brew_formula`, `github` (`owner/repo`) or `url` + `regex`.
- Use `skip_version_probe: true` for GUI apps that should not be launched during detection.
- If `uninstall` is omitted, uninstall is inferred from `install` only for known patterns (`winget`, `brew`, `npm`, `bun`, `apt-get`, `dnf`/`yum`, `pacman`).

## Releases and self-update
- `__version__` at the top of `src/RivetRook.py` drives self-update: on startup the app fetches `src/RivetRook.py` from GitHub `main` and offers to update when the published `__version__` is higher. Bump it on every release, or users are never notified.
- Update path: `git pull --ff-only` only when the script is at `<root>/src/RivetRook.py` of a clone whose `origin` is `paulocarinhena/RivetRook`; otherwise download + validate + atomic swap of `RivetRook.py` and the default `config.json`. `RIVETROOK_NO_UPDATE=1` disables it.

## Docs and install surface
- `README.md` (en, default) and `README.pt-br.md` (pt-BR) are mirrors: change both together. Images live in `assets/`; when the UI changes, regenerate the screenshot under a new versioned name (`assets/screenshot-vX.Y.Z.png`) — GitHub's CDN keeps serving stale copies of a reused file name. The animated README demo is generated from the real UI by `python assets/make_demo.py` (local-only, git-ignored; writes `assets/demo-v<__version__>.svg`); regenerate it on release and update both READMEs to the new name.
- `INSTALLATION.md` is the runbook AI agents follow ("Install RivetRook: <repo URL>"). Keep its commands idempotent and in sync with `bin/rivetrook` (POSIX sh, LF) and `bin/rivetrook.cmd` (CRLF); `.gitattributes` pins those line endings.
- `rivetrook --version` (`-V`) prints `RivetRook <__version__>` and exits without the interactive UI; installers rely on it.

## Strings and UX changes
- Any user-facing text should come from `config.json` i18n keys via `_t(...)`; update both `i18n.pt-br` and `i18n.en`.
- Keep comments/docstrings in English in source code.

## Platform behavior to preserve
- Windows command execution is via PowerShell (`pwsh` preferred); do not replace with `cmd` semantics when editing command runners.
- `needs_git` enforcement only applies on Windows (with optional winget Git install flow).
- npm global install/upgrade paths include Node major-version gating (v20+) and npm user-prefix remediation; avoid bypassing this flow for npm-based tools.
