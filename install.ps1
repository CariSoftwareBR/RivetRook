# RivetRook one-line installer for Windows (Windows PowerShell 5.1 or PowerShell 7+):
#
#   irm https://raw.githubusercontent.com/CariSoftwareBR/RivetRook/main/install.ps1 | iex
#
# Installs everything RivetRook needs (Python and PowerShell 7 via winget when
# missing), puts `rivetrook` on the PATH and leaves it ready to run in the same
# window. Idempotent: running it again updates an existing install. Mirrors
# INSTALLATION.md. Never calls `exit`: under `irm | iex` that would close the
# user's PowerShell window.

function Test-RivetRookPython {
    $probe = 'import sys; sys.exit(sys.version_info < (3, 8))'
    if (Get-Command python -ErrorAction SilentlyContinue) {
        try { & python -c $probe *> $null; if ($LASTEXITCODE -eq 0) { return $true } } catch {}
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        try { & py -3 -c $probe *> $null; if ($LASTEXITCODE -eq 0) { return $true } } catch {}
    }
    return $false
}

function Update-RivetRookSessionPath {
    # Pick up PATH entries that installers just wrote to the registry.
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user    = [Environment]::GetEnvironmentVariable('Path', 'User')
    $seen = @{}
    $merged = foreach ($p in (@($env:Path -split ';') + @($machine -split ';') + @($user -split ';'))) {
        if ($p -and -not $seen.ContainsKey($p.ToLower())) { $seen[$p.ToLower()] = $true; $p }
    }
    $env:Path = ($merged -join ';')
}

function Add-RivetRookUserPath([string]$dir) {
    # Persist $dir on the user PATH and make it visible in this session too.
    $parts = @([Environment]::GetEnvironmentVariable('Path', 'User') -split ';' | Where-Object { $_ })
    if ($parts -notcontains $dir) {
        [Environment]::SetEnvironmentVariable('Path', (($parts + $dir) -join ';'), 'User')
    }
    if (@($env:Path -split ';') -notcontains $dir) {
        $env:Path = ("$env:Path".TrimEnd(';') + ';' + $dir).TrimStart(';')
    }
}

function Install-RivetRook {
    $ProgressPreference = 'SilentlyContinue'   # Invoke-WebRequest is very slow with the progress bar on 5.1
    # Windows PowerShell 5.1 may default to TLS 1.0, which GitHub rejects.
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    } catch {}

    $repoUrl = 'https://github.com/CariSoftwareBR/RivetRook.git'
    $zipUrl  = 'https://github.com/CariSoftwareBR/RivetRook/archive/refs/heads/main.zip'
    $dir     = Join-Path $HOME 'RivetRook'
    $bin     = Join-Path $dir 'bin'

    Write-Host ''
    Write-Host '  RivetRook installer'
    Write-Host ''

    # 1. Python 3.8+ (probe by running it: the Microsoft Store alias cannot run scripts).
    if (-not (Test-RivetRookPython)) {
        if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
            Write-Host '  [X] Python 3.8+ not found and winget is not available to install it.' -ForegroundColor Red
            Write-Host '      Install Python from https://www.python.org/downloads/ and run this installer again.'
            Write-Host ''
            return
        }
        Write-Host '  Python 3.8+ not found: installing it with winget...'
        winget install -e --id Python.Python.3.14 --scope user --silent --disable-interactivity --accept-package-agreements --accept-source-agreements
        Update-RivetRookSessionPath
        if (-not (Test-RivetRookPython)) {
            # The per-user installer may not have put python.exe on PATH: add it.
            $pyExe = Get-ChildItem (Join-Path $env:LOCALAPPDATA 'Programs\Python') -Filter python.exe -Recurse -Depth 1 -ErrorAction SilentlyContinue |
                Sort-Object FullName -Descending | Select-Object -First 1
            if ($pyExe) {
                Add-RivetRookUserPath $pyExe.DirectoryName
                Add-RivetRookUserPath (Join-Path $pyExe.DirectoryName 'Scripts')
            }
        }
        if (-not (Test-RivetRookPython)) {
            Write-Host '  [X] Could not install Python automatically.' -ForegroundColor Red
            Write-Host '      Install it from https://www.python.org/downloads/ and run this installer again.'
            Write-Host ''
            return
        }
        Write-Host '  [OK] Python installed.' -ForegroundColor Green
    }

    # PowerShell 7 (pwsh) is preferred by RivetRook to run tool commands;
    # Windows PowerShell 5.1 still works, so a failure here is not fatal.
    if (-not (Get-Command pwsh -ErrorAction SilentlyContinue) -and (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host '  Installing PowerShell 7 with winget...'
        winget install -e --id Microsoft.PowerShell --silent --disable-interactivity --accept-package-agreements --accept-source-agreements
        Update-RivetRookSessionPath
    }

    # 2. Get the code: git when available (updates via git pull), zip otherwise
    #    (RivetRook then updates itself by downloading its own files).
    $hasGit = [bool](Get-Command git -ErrorAction SilentlyContinue)
    if ((Test-Path (Join-Path $dir '.git')) -and $hasGit) {
        Write-Host "  Updating $dir (git pull)..."
        git -C $dir pull --ff-only --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [X] git pull failed in $dir. Check 'git -C `"$dir`" status' and try again." -ForegroundColor Red
            return
        }
    } elseif ($hasGit -and -not (Test-Path $dir)) {
        Write-Host "  Cloning RivetRook into $dir..."
        git clone --quiet $repoUrl $dir
        if ($LASTEXITCODE -ne 0) {
            Write-Host '  [X] git clone failed.' -ForegroundColor Red
            return
        }
    } else {
        Write-Host "  Downloading RivetRook into $dir..."
        $tmp = Join-Path ([IO.Path]::GetTempPath()) ('rivetrook-' + [Guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $tmp -ErrorAction Stop | Out-Null
        try {
            $zip = Join-Path $tmp 'RivetRook-main.zip'
            Invoke-WebRequest -Uri $zipUrl -OutFile $zip -UseBasicParsing -ErrorAction Stop
            Expand-Archive -Path $zip -DestinationPath $tmp -Force -ErrorAction Stop
            $extracted = Join-Path $tmp 'RivetRook-main'
            if (-not (Test-Path (Join-Path $extracted 'src\RivetRook.py'))) {
                throw 'Downloaded archive is incomplete.'
            }
            if (Test-Path $dir) { Remove-Item $dir -Recurse -Force -ErrorAction Stop }
            Move-Item $extracted $dir -ErrorAction Stop
        } catch {
            Write-Host "  [X] Download failed: $($_.Exception.Message)" -ForegroundColor Red
            return
        } finally {
            if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue }
        }
    }

    # 3. Put RivetRook\bin on the user PATH (persistent) and on this session's PATH.
    Add-RivetRookUserPath $bin

    # Short `rivet` command (same as rivetrook), unless another `rivet` already exists.
    $alias = Join-Path $bin 'rivet.cmd'
    if (-not (Test-Path $alias) -and -not (Get-Command rivet -ErrorAction SilentlyContinue)) {
        $lines = '@echo off', 'rem Short alias for rivetrook.cmd.', 'call "%~dp0rivetrook.cmd" %*', 'exit /b %ERRORLEVEL%'
        [IO.File]::WriteAllText($alias, (($lines -join "`r`n") + "`r`n"))
    }

    # 4. Verify.
    $launcher = Join-Path $bin 'rivetrook.cmd'
    $version = & $launcher --version 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $version) {
        Write-Host "  [X] Installed, but '$launcher --version' failed." -ForegroundColor Red
        return
    }

    Write-Host ''
    Write-Host "  [OK] $version installed in $dir" -ForegroundColor Green
    if (Test-Path $alias) { Write-Host '  Run: rivetrook   (or: rivet)' } else { Write-Host '  Run: rivetrook' }
    Write-Host '  RivetRook checks for updates every time it starts.'
    Write-Host ''
}

Install-RivetRook
