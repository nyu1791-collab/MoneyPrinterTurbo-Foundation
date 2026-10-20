"""Read-only, offline preflight. Importing this module never loads app.config."""
import argparse
import json
import shutil
import sys
import tomllib
from pathlib import Path

from app.paths import runtime_root


def inspect_environment(config_path: Path | None = None) -> dict:
    """Return fixed check identifiers and statuses; never return config values."""
    checks = []

    def add(name, status, message):
        checks.append(dict(check=name, status=status, message=message))

    add("python", "ok" if sys.version_info >= (3, 11) else "error",
        "Python 3.11 or newer is required.")
    for tool in ("ffmpeg", "ffprobe"):
        add(tool, "ok" if shutil.which(tool) else "error",
            "Executable available." if shutil.which(tool) else "Install executable on PATH.")
    path = config_path if config_path is not None else runtime_root() / "config.toml"
    try:
        with path.open("rb") as stream:
            config = tomllib.load(stream)
    except FileNotFoundError:
        if config_path is not None:
            add("config", "error", "Specified configuration file does not exist.")
        else:
            add("config", "warning", "Configuration absent; create a private config.toml before generation.")
    except (OSError, ValueError):
        # TOML parser exceptions can contain the actual input, including credentials.
        add("config", "error", "Configuration unreadable or invalid TOML; values suppressed.")
    else:
        add("config", "ok", "TOML parsed; provider credentials have not been verified.")
        host = config.get("listen_host", "0.0.0.0")
        app = config.get("app", {})
        valid_host = isinstance(host, str) and bool(host.strip())
        if not valid_host:
            add("listen_host", "error", "listen_host must be a non-empty string.")
        if not isinstance(app, dict):
            add("api_access", "error", "The app configuration must be a TOML table.")
        elif not isinstance(app.get("api_key", ""), str):
            add("api_access", "error", "api_key must be a string if configured.")
        elif not valid_host:
            pass  # Binding errors are reported above; do not imply API readiness.
        elif host not in ("127.0.0.1", "::1", "localhost") and not (
            isinstance(app.get("api_key"), str) and app["api_key"].strip()
        ):
            add("api_access", "warning", "Non-loopback API binding without an API key; restrict access before starting.")
        else:
            add("api_access", "ok", "Local binding or API key configured; no authentication request performed.")
    return {"schema_version": 1, "offline": True,
            "status": "error" if any(c["status"] == "error" for c in checks)
            else "warning" if any(c["status"] == "warning" for c in checks) else "ok",
            "checks": checks}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Offline, read-only preflight; never invokes providers.")
    parser.add_argument("--config", type=Path, help="Private TOML file to inspect without printing its values")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable report")
    args = parser.parse_args(argv)
    report = inspect_environment(args.config)
    if args.json:
        print(json.dumps(report, ensure_ascii=False))
    else:
        for check in report["checks"]:
            print(f'{check["status"].upper()}: {check["check"]}: {check["message"]}')
        print("Offline preflight only; credentials, network access and video generation are unverified.")
    return 1 if report["status"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
