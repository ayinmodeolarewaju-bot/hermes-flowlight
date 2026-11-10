"""Inline frontend/engine.js into the Desktop plugin and the dashboard bundle."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "frontend" / "engine.js"
MARKER = "/*__ENGINE__*/"


def build() -> str:
    engine = ENGINE.read_text(encoding="utf-8")
    if "function mountFlowlight" not in engine:
        raise SystemExit("engine.js is missing mountFlowlight")
    digest = hashlib.sha256(engine.encode("utf-8")).hexdigest()
    header = f"/* flowlight-engine {digest} */\n"
    desktop = (ROOT / "frontend" / "desktop-shell.js").read_text(encoding="utf-8")
    dashboard = (ROOT / "frontend" / "dashboard-shell.js").read_text(encoding="utf-8")
    if MARKER not in desktop or MARKER not in dashboard:
        raise SystemExit("shell is missing the engine marker")
    desktop_out = desktop.replace(MARKER, header + engine, 1)
    dashboard_out = dashboard.replace(MARKER, header + engine, 1)
    (ROOT / "desktop").mkdir(exist_ok=True)
    (ROOT / "dashboard" / "dist").mkdir(parents=True, exist_ok=True)
    (ROOT / "desktop" / "plugin.js").write_text(desktop_out, encoding="utf-8")
    (ROOT / "dashboard" / "dist" / "index.js").write_text(dashboard_out, encoding="utf-8")
    (ROOT / "dashboard" / "dist" / "style.css").write_text(
        "/* Flowlight draws its own surface. */\n.flowlight-dash{background:#07060e;}\n",
        encoding="utf-8",
    )
    return digest


def check() -> int:
    engine = ENGINE.read_text(encoding="utf-8")
    digest = hashlib.sha256(engine.encode("utf-8")).hexdigest()
    desktop = (ROOT / "desktop" / "plugin.js").read_text(encoding="utf-8")
    dashboard = (ROOT / "dashboard" / "dist" / "index.js").read_text(encoding="utf-8")
    if f"flowlight-engine {digest}" not in desktop or f"flowlight-engine {digest}" not in dashboard:
        print("frontend bundle is stale; run python scripts/bundle_frontend.py")
        return 1
    if "function mountFlowlight" not in desktop or "function mountFlowlight" not in dashboard:
        print("bundled engine is missing")
        return 1
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        raise SystemExit(check())
    print(build())
