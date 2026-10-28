#!/usr/bin/env python3
"""Build the ChatGPT/Codex ZIP with shared skills and OAuth CIMD.

Run: python3 scripts/package_openai.py
The ZIP is a development/review draft, not proof of public submission readiness.
"""

import argparse
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def build(output_dir):
    manifest = json.loads((ROOT / "openai/plugin.json").read_text())
    mcp = json.loads((ROOT / "openai/mcp.json").read_text())
    cursor = json.loads((ROOT / ".cursor-plugin/plugin.json").read_text())
    if manifest["name"] != cursor["name"]:
        raise ValueError("The OpenAI and Cursor plugin names must match")

    interface = manifest["extensions"]["com.openai"]["interface"]
    if len(interface["shortDescription"]) > 30:
        raise ValueError("OpenAI shortDescription exceeds 30 characters")
    server = mcp["mcpServers"]["soundlink"]
    cursor_server = json.loads((ROOT / "mcp.json").read_text())["mcpServers"]["soundlink"]
    if server["url"] != cursor_server["url"]:
        raise ValueError("Both clients must connect to the same Soundlink server")
    if server.get("headers"):
        raise ValueError("Public OpenAI packages must not contain server headers")
    auth = server["extensions"]["com.openai"]["auth"]
    if auth["type"] != "oauth" or auth["client"] != {"mode": "cimd"}:
        raise ValueError("The OpenAI package must use OAuth CIMD")

    files = {
        "plugin.json": ROOT / "openai/plugin.json",
        "mcp.json": ROOT / "openai/mcp.json",
        "LICENSE": ROOT / "LICENSE",
    }
    for directory in ("assets", "skills"):
        source = ROOT / "openai/assets" if directory == "assets" else ROOT / "skills"
        for path in sorted(source.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"Symlinks are not allowed: {path}")
            if path.is_file():
                files[f"{directory}/{path.relative_to(source).as_posix()}"] = path
    for field in ("logo", "composerIcon", "logoDark", "composerIconDark"):
        if field in interface and interface[field].removeprefix("./") not in files:
            raise ValueError(f"Missing packaged asset: {interface[field]}")

    output_dir.mkdir(parents=True, exist_ok=True)
    archive_path = output_dir / f"{manifest['name']}-openai-{manifest['version']}.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, path in sorted(files.items()):
            entry = zipfile.ZipInfo(f"{manifest['name']}/{name}", (2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, path.read_bytes())
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise ValueError("Archive integrity check failed")
        for name in ("plugin.json", "mcp.json"):
            json.loads(archive.read(f"{manifest['name']}/{name}"))
    return archive_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    print(build(args.output_dir.resolve()))
    print("Draft package: review cases have not been run. Public submission also needs")
    print("publisher/country/commerce confirmation, policy coverage review, a demo video,")
    print("reviewer access, domain verification, host testing, and portal scans.")
