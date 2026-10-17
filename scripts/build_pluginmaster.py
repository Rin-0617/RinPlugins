"""plugins.json に並べたリポジトリの最新リリースから pluginmaster.json を作る。

各リポジトリの GitHub Release に置かれた zip（DalamudPackager の出力）の中にある
`<InternalName>.json` を読み、ダウンロード URL などを足して1件にする。
plugins.json の "overrides" に書いた項目は最後に上書きする。

使い方: python scripts/build_pluginmaster.py
環境変数 GITHUB_TOKEN があれば API の回数制限を避けるために使う。
"""

from __future__ import annotations

import io
import json
import os
import sys
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGINS_FILE = ROOT / "plugins.json"
OUTPUT_FILE = ROOT / "pluginmaster.json"


def request(url: str, accept: str = "application/vnd.github+json") -> bytes:
    headers = {"Accept": accept, "User-Agent": "RinPlugins"}
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
        return response.read()


def zip_asset(release: dict) -> dict | None:
    return next((a for a in release.get("assets", []) if a["name"].lower().endswith(".zip")), None)


def read_manifest(zip_bytes: bytes) -> dict:
    """zip の直下にある、InternalName を持つ json（*.deps.json 以外）を返す。"""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        for name in archive.namelist():
            if "/" in name or not name.endswith(".json") or name.endswith(".deps.json"):
                continue
            manifest = json.loads(archive.read(name).decode("utf-8-sig"))
            if isinstance(manifest, dict) and "InternalName" in manifest:
                return manifest
    raise ValueError("zip にプラグインのマニフェストがありません")


def epoch(timestamp: str) -> int:
    return int(datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp())


def build_entry(config: dict) -> dict | None:
    repo = config["repo"]
    releases = json.loads(request(f"https://api.github.com/repos/{repo}/releases?per_page=30"))
    releases = [r for r in releases if not r.get("draft") and zip_asset(r)]
    stable = next((r for r in releases if not r.get("prerelease")), None)
    newest = releases[0] if releases else None
    if newest is None:
        print(f"skip {repo}: zip 付きのリリースがありません", file=sys.stderr)
        return None

    # 安定版がなければ、テスト版だけのプラグインとして載せる。
    main = stable or newest
    asset = zip_asset(main)
    entry = read_manifest(request(asset["browser_download_url"], accept="application/octet-stream"))
    entry.setdefault("RepoUrl", f"https://github.com/{repo}")
    entry["DownloadLinkInstall"] = asset["browser_download_url"]
    entry["DownloadLinkUpdate"] = asset["browser_download_url"]
    entry["DownloadLinkTesting"] = asset["browser_download_url"]
    entry["LastUpdate"] = epoch(main["published_at"])
    entry["IsHide"] = False
    entry["IsTestingExclusive"] = stable is None

    # 安定版より新しいテスト版があれば、テスト版の配布先として載せる。
    if stable is not None and newest is not stable and newest.get("prerelease"):
        testing = read_manifest(request(zip_asset(newest)["browser_download_url"], accept="application/octet-stream"))
        entry["DownloadLinkTesting"] = zip_asset(newest)["browser_download_url"]
        entry["TestingAssemblyVersion"] = testing.get("AssemblyVersion")

    entry.update(config.get("overrides", {}))
    print(f"ok   {repo}: {entry['InternalName']} {entry.get('AssemblyVersion')} ({main['tag_name']})", file=sys.stderr)
    return entry


def main() -> int:
    configs = json.loads(PLUGINS_FILE.read_text(encoding="utf-8"))
    entries = []
    failed = False
    for config in configs:
        try:
            entry = build_entry(config)
        except Exception as error:  # 1つのリポジトリの失敗で全体を止めない
            print(f"fail {config.get('repo')}: {error}", file=sys.stderr)
            failed = True
            continue
        if entry is not None:
            entries.append(entry)

    if failed and OUTPUT_FILE.exists():
        # 取得に失敗したプラグインが配布リストから消えないよう、前回の内容を引き継ぐ。
        previous = {e["InternalName"]: e for e in json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))}
        current = {e["InternalName"] for e in entries}
        entries.extend(e for name, e in previous.items() if name not in current)

    entries.sort(key=lambda e: e["InternalName"].lower())
    OUTPUT_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
