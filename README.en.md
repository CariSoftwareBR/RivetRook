<p align="center">
  <img src="assets/banner.svg" alt="RivetRook — AI toolchain manager" width="100%">
</p>

<p align="center">
  <b>Install, update and manage every AI coding tool — from a single terminal.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8%2B-A78BFA?style=flat-square&logo=python&logoColor=white" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/node.js-20%2B-60A5FA?style=flat-square&logo=nodedotjs&logoColor=white" alt="Node.js 20+">
  <img src="https://img.shields.io/badge/windows%20·%20macOS%20·%20linux-22D3EE?style=flat-square&logo=windowsterminal&logoColor=white" alt="Windows · macOS · Linux">
  <img src="https://img.shields.io/badge/license-GPL--3.0-34D399?style=flat-square" alt="License GPL-3.0">
</p>

<p align="center">
  <a href="README.md">Português</a> &nbsp;·&nbsp; <b>English</b>
</p>

<br>

> [!TIP]
> **Install it with your AI agent.** Paste this into Claude Code, Codex, Gemini CLI, Cursor or any other agent:
>
> ```text
> Install RivetRook: https://github.com/paulocarinhena/RivetRook
> ```
>
> 🤖 *AI agents: the installation runbook is [`INSTALLATION.md`](INSTALLATION.md).*

<p align="center">
  <img src="assets/demo-v1.1.0.svg" alt="Animated RivetRook terminal demo" width="100%">
</p>

## ✦ Highlights

<table>
  <tr>
    <td width="33%" valign="top"><b>⚡ One menu, 23 tools</b><br><sub>Claude Code, Codex, Gemini CLI, Cursor, Zed and more — install, update and remove them one number away.</sub></td>
    <td width="33%" valign="top"><b>🔍 Always current</b><br><sub>Detects the installed and the latest published version in parallel, flagging what can be updated.</sub></td>
    <td width="33%" valign="top"><b>🔁 Updates itself</b><br><sub>On every start it checks GitHub and offers the new version — via <code>git pull</code> or a validated download.</sub></td>
  </tr>
  <tr>
    <td valign="top"><b>🖥️ Truly cross-platform</b><br><sub>Windows, macOS and Linux (Debian, Fedora, Arch), using <code>winget</code>, <code>brew</code>, <code>apt</code>, <code>dnf</code>, <code>pacman</code> and <code>npm</code>.</sub></td>
    <td valign="top"><b>🔑 API keys</b><br><sub>Configures and persists keys for the tools that need them, right from the menu.</sub></td>
    <td valign="top"><b>🧩 Extensible</b><br><sub>Every tool is just an entry in <code>config.json</code>. No dependencies: Python standard library only.</sub></td>
  </tr>
</table>

## 🚀 Installation

**With an AI agent** — use the sentence from the tip above. The agent follows [`INSTALLATION.md`](INSTALLATION.md), puts the `rivetrook` command on your terminal and verifies the install.

**By hand:**

```sh
git clone https://github.com/paulocarinhena/RivetRook.git
python3 RivetRook/src/RivetRook.py        # Windows: python RivetRook\src\RivetRook.py
```

To launch with a double-click, use `src/Execute_RivetRook.bat` (Windows) or `src/Execute_RivetRook.sh` (Linux/macOS). To get a `rivetrook` command in every terminal, follow [`INSTALLATION.md`](INSTALLATION.md).

> **Requirements:** Python 3.8+. Node.js 20+ is installed automatically on first run if missing.

## 🧭 Usage

On start, RivetRook asks for the language, offers its own update (when there is one), checks Node.js and shows the state of every tool. Pick one or more by number or name — `3`, `claude` or `1,3,5` — then the action: **install**, **upgrade**, **uninstall** or **configure the API key**. An empty `Enter` exits.

<details>
<summary><b>Icon legend</b></summary>
<br>

| Icon | Meaning |
|:----:|---------|
| `●` | Installed |
| `◐` | Installed, but only available through the shell profile |
| `○` | Not installed |
| `↑ x → y` | Update available |
| `⚷` | API key — green: configured · yellow: pending |

</details>

## 🧰 Supported tools

<table>
<tr><th align="left">AI CLIs</th><th align="left">IDEs</th></tr>
<tr><td valign="top">

| Tool | Author |
|------|--------|
| **claude** | Anthropic |
| **codex** | OpenAI |
| **geminicli** | Google |
| **agy** | Google · Antigravity |
| **copilot** | GitHub / Microsoft |
| **cursor-agent** | Anysphere |
| **opencode** | SST / Dax |
| **pi** | Earendil Works |
| **kilocode** | Kilo Code |
| **cline** | Cline Bot |
| **qwen** | Alibaba Cloud |
| **kimi** | Moonshot AI |
| **grok** | xAI |
| **groq** | Groq |
| **openhands** | All Hands AI |
| **forgecode** | Forge |
| **crush** | Charmbracelet |

</td><td valign="top">

| IDE | Author |
|-----|--------|
| **cursor** | Anysphere |
| **zed** | Zed Industries |
| **windsurf** | Codeium / Windsurf |
| **antigravity** | Google |
| **trae** | ByteDance / Trae |
| **opencode-desktop** | Anomaly |

</td></tr>
</table>

Missing one? Adding it means editing `config.json` — see below.

## 📚 Reference

<details>
<summary><b>Self-update</b></summary>
<br>

On start, RivetRook compares its <code>__version__</code> with the one published on the GitHub `main` branch. When a newer version exists, it offers to update and restart:

- **Git clone** of this repository → `git pull --ff-only`
- **Standalone copy** → downloads `src/RivetRook.py` and `src/config.json`, validates both and only then replaces the files (a `config.json` passed as an argument is never touched)

To disable it, set the environment variable `RIVETROOK_NO_UPDATE=1`.

</details>

<details>
<summary><b>API keys</b></summary>
<br>

For tools that need a key, RivetRook:

- detects whether the key is already configured;
- asks for it right after installation;
- saves it to the tool's own config file (e.g. `~/.claude.json`);
- persists it as an environment variable in shell files (`.bashrc`, `.zshrc`, `.profile`) on Linux/macOS.

To configure it later, pick the tool in the menu and choose **4 – Configure API key**.

</details>

<details>
<summary><b>Adding a tool</b></summary>
<br>

Each tool is an entry in `src/config.json`, under `"tools"` or `"ides"` (menu order follows JSON order):

```jsonc
"my-tool": {
  "author": "Company",
  "description": "Descrição em português",
  "description_en": "Description in English",
  "install": {
    "all": "npm install -g my-tool",
    "windows": "winget install -e --id Company.Tool",
    "macos": "brew install my-tool",
    "linux": { "debian": "apt-get install -y my-tool", "default": "npm install -g my-tool" }
  },
  "upgrade": { "all": "npm install -g my-tool@latest" },
  "uninstall": { "all": "npm uninstall -g my-tool" },
  "run": "my-tool"
}
```

| Field | Description |
|-------|-------------|
| `author`, `description`, `description_en` | Author and descriptions shown in the menu |
| `install` · `upgrade` · `uninstall` | Commands per platform: `all`, `windows`, `macos`, `linux` (or `debian`/`fedora`/`arch`/`default`). Without `uninstall`, it is inferred from `install` for `winget`, `brew`, `npm`, `bun`, `apt-get`, `dnf`/`yum` and `pacman` |
| `run` | Main binary, used to detect the installation |
| `version_cmd` · `version_regex` | Command and regex (group 1) to read the installed version |
| `latest` | Where to look up the latest version: `npm`, `pypi`, `brew_cask`, `brew_formula`, `github` (`owner/repo`) or `url` + `regex`. Inferred automatically for `npm`, `bun` and `brew` installs |
| `skip_version_probe` | Don't run the binary to detect the version (GUI apps) |
| `needs_git` | Requires Git on Windows |
| `path_entry` | Folder to add to `PATH` after installing |
| `configure` | API key: `env_var`, `settings_file`, `settings_key`, `prompt` |

To contribute a new tool, see [`CONTRIBUTING.md`](CONTRIBUTING.md).

</details>

<details>
<summary><b>Package managers by platform</b></summary>
<br>

| Platform | Package managers |
|----------|------------------|
| Windows | `winget`, PowerShell 7 (`pwsh`), `npm` |
| macOS | `brew`, `npm`, `curl` |
| Debian / Ubuntu | `apt`, `npm`, `curl` |
| Fedora / RHEL | `dnf`, `npm`, `curl` |
| Arch | `pacman`, `npm`, `curl` |

</details>

<details>
<summary><b>Disclaimer</b></summary>
<br>

RivetRook is only an installation helper: it runs the official commands published by each vendor (`npm`, `winget`, `brew`, `apt`…), exactly as you would in a terminal. It does not modify, redistribute or claim ownership of any third-party software, and it is not affiliated with the companies listed — every tool belongs to its respective owner.

</details>

## 🤝 Contributing

Bugs, ideas and new tools are welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md).

<br>

<p align="center">
  <sub>Made with 💜 by <a href="https://github.com/paulocarinhena">Paulo Carinhena</a> · <a href="LICENSE">GPL-3.0</a> license</sub>
</p>
