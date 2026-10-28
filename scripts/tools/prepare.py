"""准备运行依赖：Python 虚拟环境、pip 依赖、前端 node_modules。

由 start.bat / start.sh 在 bootstrap 之后调用，负责“装错就修”：
- 虚拟环境缺失、损坏、Python 版本过低 → 自动重建
- requirements.txt 变化 → 重装 Python 依赖
- node_modules 缺失、node 大版本变化、lock 文件变化 → 重装前端依赖

用法：
    python scripts/tools/prepare.py --root <项目根> [--repair] [--venv <路径>] [--skip-npm]
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

MIN_PY = (3, 10)
MIN_NODE = 18
WIN = os.name == "nt"
MARKER = ".jd_env"
MIRROR_NPM = "https://registry.npmmirror.com"
MIRROR_PIP = "https://pypi.tuna.tsinghua.edu.cn/simple"


def say(msg: str = "") -> None:
    print(msg, flush=True)


def run(
    cmd: list[str], cwd: Path | None = None, capture: bool = True
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        text=True,
        errors="replace",
    )


def tail(text: str | None, lines: int = 12) -> str:
    if not text:
        return ""
    rows = [row for row in text.strip().splitlines() if row.strip()]
    return "\n".join("      " + row for row in rows[-lines:])


def md5_of(*paths: Path) -> str:
    digest = hashlib.md5()
    for path in paths:
        if path.exists():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if WIN else "bin/python")


def probe_python(exe: Path) -> tuple[int, int] | None:
    if not exe.exists():
        return None
    result = run([str(exe), "-c", "import sys;print('%d %d' % sys.version_info[:2])"])
    if result.returncode != 0:
        return None
    try:
        major, minor = result.stdout.strip().split()
        return int(major), int(minor)
    except ValueError:
        return None


def ensure_venv(root: Path, venv: Path, repair: bool) -> tuple[Path, str]:
    exe = venv_python(venv)
    version = None if repair else probe_python(exe)

    if version and version >= MIN_PY:
        say(f"   - 虚拟环境正常（Python {version[0]}.{version[1]}），跳过创建")
    else:
        if venv.exists():
            reason = "强制重建" if repair else ("版本过低" if version else "环境损坏")
            say(f"   - 虚拟环境{reason}，正在重建 ...")
            shutil.rmtree(venv, ignore_errors=True)
        else:
            try:
                shown = venv.relative_to(root).as_posix()
            except ValueError:
                shown = str(venv)
            say(f"   - 创建 Python 虚拟环境 {shown} ...")
        result = run([sys.executable, "-m", "venv", str(venv)], capture=False)
        if result.returncode != 0:
            raise RuntimeError("虚拟环境创建失败，请确认 Python 安装完整")
        version = probe_python(exe)
        if not version or version < MIN_PY:
            raise RuntimeError("虚拟环境创建后不可用，请删除 backend/.venv 后重试")

    # pip 自检
    pip_ok = run([str(exe), "-m", "pip", "--version"]).returncode == 0
    if not pip_ok:
        say("   - pip 缺失，正在修复 ...")
        run([str(exe), "-m", "ensurepip", "--upgrade"], capture=False)
        run([str(exe), "-m", "pip", "install", "--upgrade", "pip", "--quiet"])
        if run([str(exe), "-m", "pip", "--version"]).returncode != 0:
            raise RuntimeError("pip 修复失败，请手动执行 backend/.venv/Scripts/python -m ensurepip")

    return exe, f"{version[0]}.{version[1]}"


def install_python_deps(root: Path, exe: Path, venv: Path, repair: bool) -> None:
    requirements = root / "requirements.txt"
    if not requirements.exists():
        raise RuntimeError(f"缺少依赖清单：{requirements}")

    want = md5_of(requirements)
    marker = venv / ".req_hash"
    current = marker.read_text(encoding="utf-8").strip() if marker.exists() else ""

    if not repair and current == want:
        say("   - Python 依赖无变化，跳过安装")
        return

    say("   - 安装 Python 依赖 requirements.txt ...")
    result = run([str(exe), "-m", "pip", "install", "-r", str(requirements), "--quiet"])
    if result.returncode != 0:
        say("   - 默认源安装失败，切换国内镜像重试 ...")
        result = run(
            [str(exe), "-m", "pip", "install", "-r", str(requirements), "-i", MIRROR_PIP, "--quiet"]
        )
    if result.returncode != 0:
        raise RuntimeError("Python 依赖安装失败：\n" + tail(result.stdout))

    marker.write_text(want, encoding="utf-8")


def node_version() -> tuple[tuple[int, int, int], str] | None:
    node = shutil.which("node")
    if not node:
        return None
    result = run([node, "-v"])
    if result.returncode != 0:
        return None
    raw = result.stdout.strip().lstrip("vV")
    try:
        parts = [int(x) for x in raw.split(".")[:3]]
        while len(parts) < 3:
            parts.append(0)
        return (parts[0], parts[1], parts[2]), node
    except ValueError:
        return None


def install_app_deps(root: Path, app: str, node_major: int, repair: bool) -> None:
    app_dir = root / app
    modules = app_dir / "node_modules"
    lock = app_dir / "package-lock.json"
    pkg = app_dir / "package.json"

    if not pkg.exists():
        say(f"   - 跳过 {app}（未找到 package.json）")
        return

    want = f"node{node_major}-{md5_of(lock, pkg)}"
    marker = modules / MARKER
    current = marker.read_text(encoding="utf-8").strip() if marker.exists() else ""

    if not repair and modules.exists() and current == want:
        say(f"   - {app} 依赖无变化，跳过安装")
        return

    npm = shutil.which("npm")
    if not npm:
        raise RuntimeError("未找到 npm，请确认 Node.js 安装完整")

    reason = "强制重装" if repair else ("依赖变更" if modules.exists() else "首次安装")
    say(f"   - 安装 {app} 依赖（{reason}）...")
    result = run([npm, "install", "--no-audit", "--no-fund"], cwd=app_dir)
    if result.returncode != 0:
        say("   - npm 默认源失败，切换国内镜像重试 ...")
        result = run(
            [npm, "install", "--no-audit", "--no-fund", "--registry", MIRROR_NPM], cwd=app_dir
        )
    if result.returncode != 0:
        raise RuntimeError(f"{app} 依赖安装失败：\n" + tail(result.stdout))

    modules.mkdir(parents=True, exist_ok=True)
    # npm 安装过程可能重写 lock 文件，这里按安装后的内容记录标记
    marker.write_text(f"node{node_major}-{md5_of(lock, pkg)}", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="项目根目录")
    parser.add_argument("--venv", default=None, help="虚拟环境路径，默认 backend/.venv")
    parser.add_argument("--repair", action="store_true", help="强制重建虚拟环境并重装依赖")
    parser.add_argument("--skip-npm", action="store_true", help="跳过前端依赖")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    venv = Path(args.venv).resolve() if args.venv else root / "backend" / ".venv"

    try:
        exe, py_ver = ensure_venv(root, venv, args.repair)
        install_python_deps(root, exe, venv, args.repair)

        node = node_version()
        if not node:
            raise RuntimeError("未检测到可用的 Node.js，请先执行 scripts/bootstrap.ps1")
        (major, minor, patch), node_path = node
        if major < MIN_NODE:
            raise RuntimeError(f"Node.js v{major}.{minor}.{patch} 过低，需要 {MIN_NODE}+")
        say(f"   - Node.js v{major}.{minor}.{patch}（{node_path}）")

        if not args.skip_npm:
            install_app_deps(root, "web", major, args.repair)
            install_app_deps(root, "admin", major, args.repair)

        say(f"   - 依赖就绪：Python {py_ver} / Node.js v{major}.{minor}.{patch}")
        return 0
    except Exception as exc:  # noqa: BLE001
        say(f"   [失败] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
