# =============================================================================
#  运行环境自举（Windows）
#  目标：没有 Python / Node，或版本过低时，自动下载便携版本并写入 env.cmd
#  用法：powershell -NoProfile -ExecutionPolicy Bypass -File scripts\bootstrap.ps1
#        可选：-DryRun（只检测不安装）  -ForceNode / -ForcePython（强制重装）
#  产物：<项目>\.runtime\{node-v*, python-*}、scripts\logs\env.cmd、bootstrap.log
# =============================================================================
[CmdletBinding()]
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [switch]$ForceNode,
    [switch]$ForcePython,
    [switch]$IgnoreSystem,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

# 某些环境里会同时存在 http_proxy 与 HTTP_PROXY，PowerShell 创建子进程时会因此报
# “字典中的关键字重复”，导致 curl / 安装器静默失败。这里做一次去重（保留第一个）。
function Repair-DuplicateEnv {
    try {
        $items = @(Get-ChildItem Env: -ErrorAction Stop)
    } catch {
        # 环境块里已存在大小写重复的键，PowerShell 无法枚举，跳过即可
        return -1
    }
    $seen = @{}
    $removed = 0
    foreach ($item in $items) {
        $key = $item.Name.ToLowerInvariant()
        if ($seen.ContainsKey($key)) {
            try {
                Remove-Item -LiteralPath ("Env:" + $item.Name) -ErrorAction Stop
                $removed++
            } catch { }
        } else {
            $seen[$key] = $true
        }
    }
    return $removed
}

# ---- 版本要求 ---------------------------------------------------------------
$PyMin      = [version]'3.10.0'
$PyTarget   = '3.12.8'
$NodeMin    = [version]'18.0.0'
$NodeTarget = '22.14.0'

$Runtime = Join-Path $Root '.runtime'
$Cache   = Join-Path $Runtime '_cache'
$LogDir  = Join-Path $Root 'scripts\logs'
$LogFile = Join-Path $LogDir 'bootstrap.log'
foreach ($dir in @($Runtime, $Cache, $LogDir)) {
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
}

function Write-Log {
    param([string]$Text, [string]$Color = 'Gray')
    Write-Host $Text -ForegroundColor $Color
    try {
        Add-Content -LiteralPath $LogFile -Value ("[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Text) -Encoding UTF8
    } catch { }
}
function Write-Info($t) { Write-Log ("   - " + $t) }
function Write-Ok($t) { Write-Log ("   [OK] " + $t) 'Green' }
function Write-Tip($t) { Write-Log ("   [提示] " + $t) 'Yellow' }
function Write-Bad($t) { Write-Log ("   [失败] " + $t) 'Red' }

# ---- 架构 -------------------------------------------------------------------
$archRaw = $env:PROCESSOR_ARCHITECTURE
if (-not $archRaw) { $archRaw = $env:PROCESSOR_ARCHITEW6432 }
$Arch = switch -Regex ($archRaw) {
    'ARM64' { 'arm64' }
    'AMD64|x64' { 'x64' }
    'x86' { 'x86' }
    default { if ([Environment]::Is64BitOperatingSystem) { 'x64' } else { 'x86' } }
}

# ---- 探测工具 ---------------------------------------------------------------
function Get-ExePath([string]$Name) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { return $cmd.Source }
    return $null
}

function Test-StoreAlias([string]$Path) {
    if (-not $Path) { return $false }
    return ($Path -like '*\WindowsApps\*')
}

function Get-PythonVersion([string]$Exe) {
    if (-not $Exe -or -not (Test-Path $Exe) -or (Test-StoreAlias $Exe)) { return $null }
    try {
        $out = & $Exe -c "import sys;print('%d.%d.%d' % sys.version_info[:3])" 2>$null
        if ($LASTEXITCODE -eq 0 -and $out) { return [version]($out.Trim()) }
    } catch { }
    return $null
}

function Get-NodeVersion([string]$Exe) {
    if (-not $Exe -or -not (Test-Path $Exe)) { return $null }
    try {
        $out = & $Exe -v 2>$null
        if ($LASTEXITCODE -eq 0 -and $out) { return [version]($out.Trim().TrimStart('v', 'V')) }
    } catch { }
    return $null
}

# 环境变量里没有 PATH 时，也去常见安装位置找一遍
function Get-NodeCandidates {
    $list = New-Object System.Collections.ArrayList
    $cmd = Get-ExePath 'node'
    if ($cmd) { [void]$list.Add($cmd) }

    $fixed = @()
    if ($env:ProgramFiles) { $fixed += (Join-Path $env:ProgramFiles 'nodejs\node.exe') }
    if (${env:ProgramFiles(x86)}) { $fixed += (Join-Path ${env:ProgramFiles(x86)} 'nodejs\node.exe') }
    if ($env:NVM_SYMLINK) { $fixed += (Join-Path $env:NVM_SYMLINK 'node.exe') }

    $dirs = @()
    if ($env:APPDATA) { $dirs += (Join-Path $env:APPDATA 'nvm') }
    if ($env:LOCALAPPDATA) {
        $dirs += (Join-Path $env:LOCALAPPDATA 'nvm')
        $dirs += (Join-Path $env:LOCALAPPDATA 'Programs\nodejs')
    }
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) { continue }
        $fixed += (Join-Path $dir 'node.exe')
        Get-ChildItem -LiteralPath $dir -Directory -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending |
            ForEach-Object { $fixed += (Join-Path $_.FullName 'node.exe') }
    }
    foreach ($p in $fixed) { if ($p -and (Test-Path $p)) { [void]$list.Add($p) } }
    return ($list | Select-Object -Unique)
}

function Get-PythonCandidates {
    $list = New-Object System.Collections.ArrayList
    foreach ($name in @('python', 'python3')) {
        $p = Get-ExePath $name
        if ($p) { [void]$list.Add($p) }
    }
    $patterns = @()
    if ($env:LOCALAPPDATA) { $patterns += (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python3*\python.exe') }
    if ($env:ProgramFiles) { $patterns += (Join-Path $env:ProgramFiles 'Python3*\python.exe') }
    $patterns += 'C:\Python3*\python.exe'
    foreach ($pattern in $patterns) {
        Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending |
            ForEach-Object { [void]$list.Add($_.FullName) }
    }
    $py = Get-ExePath 'py'
    if ($py) {
        try {
            $out = & $py -3 -c "import sys;print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $out) { [void]$list.Add($out.Trim()) }
        } catch { }
    }
    return ($list | Select-Object -Unique)
}

# ---- 下载与解压 -------------------------------------------------------------
function Invoke-Download {
    param([string[]]$Urls, [string]$Dest, [int]$MinBytes = 1MB)
    $curl = Get-ExePath 'curl.exe'

    foreach ($url in $Urls) {
        foreach ($mode in @('proxy', 'direct')) {
            if (Test-Path $Dest) { Remove-Item -LiteralPath $Dest -Force -ErrorAction SilentlyContinue }
            $label = if ($mode -eq 'direct') { '（改为直连重试）' } else { '' }
            Write-Info ("下载 " + $url + $label)

            # 方式一：curl（快，但依赖子进程与环境块正常）
            if ($curl) {
                try {
                    $params = @('-sS', '--no-progress-meter', '-L', '--fail', '--retry', '2', '--connect-timeout', '20', '--max-time', '900', '-o', $Dest)
                    if ($mode -eq 'direct') { $params += @('--noproxy', '*') }
                    $params += $url
                    & $curl @params 2>$null
                } catch { }
            }
            if ((Test-Path $Dest) -and ((Get-Item -LiteralPath $Dest).Length -ge $MinBytes)) { return $true }

            # 方式二：进程内下载（不创建子进程，规避环境块异常）
            $oldProxy = $null
            try {
                $oldProxy = [System.Net.WebRequest]::DefaultWebProxy
                if ($mode -eq 'direct') { [System.Net.WebRequest]::DefaultWebProxy = $null }
                Invoke-WebRequest -Uri $url -OutFile $Dest -UseBasicParsing -TimeoutSec 900
            } catch {
                Write-Tip ("下载失败：" + $_.Exception.Message)
            } finally {
                try { [System.Net.WebRequest]::DefaultWebProxy = $oldProxy } catch { }
            }
            if ((Test-Path $Dest) -and ((Get-Item -LiteralPath $Dest).Length -ge $MinBytes)) { return $true }

            $size = if (Test-Path $Dest) { (Get-Item -LiteralPath $Dest).Length } else { 0 }
            Write-Tip ("下载内容不完整，已获取 " + $size + " 字节")
        }
    }
    return $false
}

function Expand-ZipTo {
    param([string]$Zip, [string]$Dest)
    if (Test-Path $Dest) { Remove-Item -LiteralPath $Dest -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $Dest | Out-Null
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop
        [System.IO.Compression.ZipFile]::ExtractToDirectory($Zip, $Dest)
    } catch {
        Expand-Archive -LiteralPath $Zip -DestinationPath $Dest -Force
    }
}

# ---- Node.js ---------------------------------------------------------------
function Resolve-Node {
    if (-not $ForceNode -and -not $IgnoreSystem) {
        $best = $null
        foreach ($candidate in (Get-NodeCandidates)) {
            $v = Get-NodeVersion $candidate
            if ($v -and $v -ge $NodeMin -and (-not $best -or $v -gt $best.Version)) {
                $best = @{ Exe = $candidate; Version = $v }
            }
        }
        if ($best) {
            Write-Ok ("Node.js v{0}（{1}）" -f $best.Version, $best.Exe)
            return @{ Dir = (Split-Path -Parent $best.Exe); Exe = $best.Exe; Version = $best.Version }
        }
        $any = $null
        foreach ($candidate in (Get-NodeCandidates)) {
            $v = Get-NodeVersion $candidate
            if ($v -and (-not $any -or $v -gt $any.Version)) { $any = @{ Exe = $candidate; Version = $v } }
        }
        if ($any) { Write-Tip ("系统 Node.js v{0} 低于要求的 {1}，将使用 .runtime 便携版或自动下载 v{2}" -f $any.Version, $NodeMin, $NodeTarget) }
        else { Write-Tip ("未检测到可用的 Node.js（需要 {0}+），将使用 .runtime 便携版或自动下载 v{1}" -f $NodeMin, $NodeTarget) }
    }

    $ver = $NodeTarget
    $dir = Join-Path $Runtime "node-v$ver"
    $exe = Join-Path $dir 'node.exe'

    if ((Test-Path $exe) -and -not $ForceNode) {
        $v = Get-NodeVersion $exe
        if ($v -and $v -ge $NodeMin) {
            Write-Ok ("Node.js v{0}（复用 .runtime 中的便携版）" -f $v)
            return @{ Dir = $dir; Exe = $exe; Version = $v }
        }
    }

    if ($DryRun) {
        Write-Info ("[DryRun] 将下载 node-v{0}-win-{1}.zip 并解压到 .runtime" -f $ver, $Arch)
        return $null
    }

    $zipName = "node-v$ver-win-$Arch.zip"
    $zip = Join-Path $Cache $zipName
    if (-not (Test-Path $zip)) {
        $urls = @(
            "https://registry.npmmirror.com/-/binary/node/v$ver/$zipName",
            "https://npmmirror.com/mirrors/node/v$ver/$zipName",
            "https://nodejs.org/dist/v$ver/$zipName"
        )
        if (-not (Invoke-Download -Urls $urls -Dest $zip -MinBytes 5MB)) {
            throw "Node.js 下载失败，请检查网络或手动安装 Node.js 18+ 后重试"
        }
    }

    Write-Info "解压 Node.js ..."
    $tmp = Join-Path $Runtime '_tmp_node'
    Expand-ZipTo -Zip $zip -Dest $tmp
    $inner = Join-Path $tmp "node-v$ver-win-$Arch"
    if (-not (Test-Path $inner)) {
        $inner = (Get-ChildItem -LiteralPath $tmp -Directory | Select-Object -First 1).FullName
    }
    if (Test-Path $dir) { Remove-Item -LiteralPath $dir -Recurse -Force }
    Move-Item -LiteralPath $inner -Destination $dir
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue

    $v = Get-NodeVersion $exe
    if (-not $v) { throw "Node.js 解压后无法运行：$exe" }
    Write-Ok ("Node.js v{0} 已安装到 .runtime\{1}" -f $v, (Split-Path -Leaf $dir))
    return @{ Dir = $dir; Exe = $exe; Version = $v }
}

# ---- Python ----------------------------------------------------------------
function Find-SystemPython {
    $best = $null
    foreach ($p in (Get-PythonCandidates)) {
        $v = Get-PythonVersion $p
        if ($v -and $v -ge $PyMin -and (-not $best -or $v -gt $best.Version)) {
            $best = @{ Exe = $p; Version = $v }
        }
    }
    return $best
}

function Resolve-Python {
    if (-not $ForcePython -and -not $IgnoreSystem) {
        $sys = Find-SystemPython
        if ($sys) {
            Write-Ok ("Python {0}（{1}）" -f $sys.Version, $sys.Exe)
            return @{ Exe = $sys.Exe; Version = $sys.Version }
        }
        Write-Tip ("未检测到 Python {0}+，将使用或安装便携版 {1}（装在 .runtime，不需要管理员权限）" -f $PyMin, $PyTarget)
    }

    $ver = $PyTarget
    $dir = Join-Path $Runtime "python-$ver"
    $exe = Join-Path $dir 'python.exe'

    if ((Test-Path $exe) -and -not $ForcePython) {
        $v = Get-PythonVersion $exe
        if ($v -and $v -ge $PyMin) {
            Write-Ok ("Python {0}（复用 .runtime 中的便携版）" -f $v)
            return @{ Exe = $exe; Version = $v }
        }
    }

    if ($DryRun) {
        Write-Info ("[DryRun] 将下载 Python {0} 安装包并静默安装到 .runtime" -f $ver)
        return $null
    }

    $suffix = switch ($Arch) {
        'x64' { 'amd64' }
        'arm64' { 'arm64' }
        default { '' }
    }
    $fileName = if ($suffix) { "python-$ver-$suffix.exe" } else { "python-$ver.exe" }
    $installer = Join-Path $Cache $fileName

    if (-not (Test-Path $installer)) {
        $urls = @(
            "https://mirrors.huaweicloud.com/python/$ver/$fileName",
            "https://registry.npmmirror.com/-/binary/python/$ver/$fileName",
            "https://www.python.org/ftp/python/$ver/$fileName"
        )
        if (-not (Invoke-Download -Urls $urls -Dest $installer -MinBytes 5MB)) {
            throw "Python 安装包下载失败，请检查网络或手动安装 Python 3.10+ 后重试"
        }
    }

    Write-Info "静默安装 Python $ver（约 1 分钟）..."
    $argString = "/quiet InstallAllUsers=0 TargetDir=`"$dir`" Include_pip=1 Include_launcher=0 Include_test=0 PrependPath=0 Shortcuts=0 AssociateFiles=0 CompileAll=0"
    $code = 0
    $launched = $false
    try {
        $proc = Start-Process -FilePath $installer -ArgumentList $argString -Wait -PassThru
        $code = $proc.ExitCode
        $launched = $true
    } catch {
        Write-Tip ("Start-Process 不可用，改为直接调用：" + $_.Exception.Message)
    }
    if (-not $launched) {
        # 直接调用不会等待 GUI 安装器，这里轮询进程是否退出
        & $installer $argString
        $procName = [System.IO.Path]::GetFileNameWithoutExtension($installer)
        $deadline = (Get-Date).AddMinutes(6)
        while ((Get-Date) -lt $deadline) {
            Start-Sleep -Seconds 2
            if (-not (Get-Process -Name $procName -ErrorAction SilentlyContinue)) { break }
        }
    }
    if ($code -ne 0 -and $code -ne 3010) {
        if (-not $launched -and (Test-Path $exe)) { $code = 0 }
    }
    if ($code -ne 0 -and $code -ne 3010) {
        throw "Python 安装失败（退出码 $code），可尝试手动安装 Python 3.10+"
    }

    $v = Get-PythonVersion $exe
    if (-not $v) { throw "Python 安装后无法运行：$exe" }
    Write-Ok ("Python {0} 已安装到 .runtime\{1}" -f $v, (Split-Path -Leaf $dir))
    return @{ Exe = $exe; Version = $v }
}

# ---- 输出 env.cmd ----------------------------------------------------------
function Write-EnvCmd {
    param($Python, $Node)
    $lines = @(
        '@echo off',
        'rem 由 scripts\bootstrap.ps1 自动生成，请勿手工修改',
        "set `"SYS_PY=$($Python.Exe)`""
    )
    if ($Node -and $Node.Dir) {
        $lines += "set `"JD_NODE_DIR=$($Node.Dir)`""
        $lines += "set `"PATH=$($Node.Dir);%PATH%`""
    } else {
        $lines += 'set "JD_NODE_DIR="'
    }
    $path = Join-Path $LogDir 'env.cmd'
    Set-Content -LiteralPath $path -Value $lines -Encoding Default
    Write-Info ("环境变量已写入 scripts\logs\env.cmd")
}

# ---- 主流程 ----------------------------------------------------------------
Write-Log "== 运行环境检查（架构 $Arch，PowerShell $($PSVersionTable.PSVersion)）=="
$deduped = Repair-DuplicateEnv
if ($deduped -gt 0) {
    Write-Tip ("已清理 $deduped 个大小写重复的环境变量，避免子进程启动失败")
} elseif ($deduped -lt 0) {
    Write-Tip "检测到大小写重复的环境变量，已切换兼容模式继续"
}

try {
    $node = Resolve-Node
    $python = Resolve-Python

    if ($DryRun) {
        Write-Log "== DryRun 结束 =="
        exit 0
    }

    if (-not $node) { throw "Node.js 环境未就绪" }
    if (-not $python) { throw "Python 环境未就绪" }

    Write-EnvCmd -Python $python -Node $node
    Write-Log "== 环境就绪：Python $($python.Version) / Node.js v$($node.Version) =="
    exit 0
} catch {
    Write-Bad $_.Exception.Message
    Write-Info ("详细日志：" + $LogFile)
    exit 1
}
