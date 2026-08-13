#Requires -Version 5.1
<#
.SYNOPSIS
    xiaohongshu-publish 环境检查与自动安装。
.DESCRIPTION
    检查 Python 3 / Node.js / Microsoft Edge / playwright-core 四项依赖，
    并用 npm 把 playwright-core 安装到仓库本地 node_modules（需要联网）。
.PARAMETER SkipInstall
    只检查，不安装任何依赖。
.PARAMETER Force
    即使 playwright-core 已存在也重新安装。
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
#>
[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot

function Write-Step { param([string]$Msg) Write-Host "==> $Msg" -ForegroundColor Cyan }
function Write-Ok   { param([string]$Msg) Write-Host "  [OK] $Msg" -ForegroundColor Green }
function Write-Warn { param([string]$Msg) Write-Host "  [WARN] $Msg" -ForegroundColor Yellow }
function Write-Fail { param([string]$Msg) Write-Host "  [FAIL] $Msg" -ForegroundColor Red }

# 查找 Python 3：优先 PATH，其次 Codex 主运行库自带 Python
function Find-Python3 {
    foreach ($cand in @('python', 'py', 'python3')) {
        $cmd = Get-Command $cand -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        $ver = (& $cmd.Source --version 2>&1 | Out-String).Trim()
        if ($ver -match 'Python 3\.') { return @{ Path = $cmd.Source; Version = $ver } }
    }
    $fallback = "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path -LiteralPath $fallback) {
        $ver = (& $fallback --version 2>&1 | Out-String).Trim()
        if ($ver -match 'Python 3\.') { return @{ Path = $fallback; Version = $ver } }
    }
    return $null
}

# 查找 Node.js：优先 PATH，其次 Codex cua_node 运行库（随版本变化的目录）
function Find-Node {
    $cmd = Get-Command node -ErrorAction SilentlyContinue
    if ($cmd) {
        $ver = (& $cmd.Source --version 2>&1 | Out-String).Trim()
        return @{ Path = $cmd.Source; Version = $ver; NpmFromPath = $true; BinDir = $null }
    }
    $runtimeRoot = Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\runtimes\cua_node'
    $fallback = Get-ChildItem -LiteralPath $runtimeRoot -Directory -ErrorAction SilentlyContinue |
        ForEach-Object { Join-Path $_.FullName 'bin\node.exe' } |
        Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if ($fallback) {
        $ver = (& $fallback --version 2>&1 | Out-String).Trim()
        return @{ Path = $fallback; Version = $ver; NpmFromPath = $false; BinDir = Split-Path -Parent $fallback }
    }
    return $null
}

$issues = 0

# 1. Python 3
Write-Step '检查 Python 3 ...'
$py = $null
$pyInfo = Find-Python3
if ($pyInfo) {
    $py = $pyInfo.Path
    Write-Ok "Python 3 已找到：$($pyInfo.Version)（$py）"
} else {
    Write-Warn '未找到 Python 3（build_publish_pack.py 需要，仅用标准库）'
    $issues++
}

# 2. Node.js / npm
Write-Step '检查 Node.js ...'
$node = $null
$npm = $null
$nodeInfo = Find-Node
if ($nodeInfo) {
    $node = $nodeInfo.Path
    Write-Ok "Node.js 已找到：$($nodeInfo.Version)（$node）"
    if ($nodeInfo.NpmFromPath) {
        $npm = (Get-Command npm -ErrorAction SilentlyContinue).Source
        if (-not $npm) { Write-Warn '未找到 npm（Node.js 安装可能不完整）'; $issues++ }
    } else {
        $npm = Join-Path $nodeInfo.BinDir 'npm.cmd'
        if (-not (Test-Path -LiteralPath $npm)) { Write-Warn "未找到 npm：$npm"; $issues++ }
    }
} else {
    Write-Warn '未找到 Node.js（pw-bridge.cjs 需要）'
    $issues++
}

# 3. Microsoft Edge
Write-Step '检查 Microsoft Edge ...'
$edgeCandidates = @(
    (Join-Path ${env:ProgramFiles(x86)} 'Microsoft\Edge\Application\msedge.exe'),
    (Join-Path $env:ProgramFiles 'Microsoft\Edge\Application\msedge.exe'),
    (Join-Path $env:LOCALAPPDATA 'Microsoft\Edge\Application\msedge.exe')
)
$edge = $edgeCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if ($edge) { Write-Ok "Microsoft Edge 已找到：$edge" }
else { Write-Warn '未找到 Microsoft Edge（仅浏览器自动化需要，手动/半自动发布不受影响）' }

# 4. playwright-core
Write-Step '检查 playwright-core ...'
$localModules = Join-Path $repoRoot 'node_modules'
$localPw = Join-Path $localModules 'playwright-core'
if (-not $node) {
    Write-Warn '无 Node.js，无法安装 playwright-core'
    $issues++
} elseif ((Test-Path -LiteralPath $localPw) -and -not $Force) {
    Write-Ok "playwright-core 已存在：$localPw"
} elseif ($SkipInstall) {
    Write-Warn 'playwright-core 缺失（已指定 -SkipInstall，未安装）'
    $issues++
} elseif (-not $npm) {
    Write-Warn '无 npm，无法安装 playwright-core'
    $issues++
} else {
    Write-Step '安装 playwright-core（npm install，需要联网）...'
    & $npm install --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) {
        Write-Fail 'npm install 失败，请检查网络后重试'
        $issues++
    } elseif (Test-Path -LiteralPath $localPw) {
        Write-Ok 'playwright-core 已安装到仓库本地 node_modules'
    } else {
        Write-Fail 'npm install 结束但未找到 playwright-core'
        $issues++
    }
}

# 5. 验证
Write-Step '验证 ...'
if ($py) {
    & $py scripts/build_publish_pack.py --help | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Ok 'build_publish_pack.py 可运行（--help 正常）' }
    else { Write-Fail 'build_publish_pack.py 运行异常'; $issues++ }
}
if ($node -and (Test-Path -LiteralPath $localPw)) {
    $check = & $node -e "require('playwright-core'); console.log('ok')" 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) { Write-Ok 'playwright-core 可正常加载' }
    else { Write-Fail "playwright-core 加载失败：$($check.Trim())"; $issues++ }
}

Write-Host ''
if ($issues -eq 0) {
    Write-Host '环境就绪，可以开始使用。' -ForegroundColor Green
} else {
    Write-Host "存在 $issues 项待处理，请根据上方提示补齐。" -ForegroundColor Yellow
    exit 1
}
