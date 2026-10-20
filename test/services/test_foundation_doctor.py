import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

from app.doctor import inspect_environment

ROOT = Path(__file__).resolve().parents[2]


def test_missing_config_does_not_create_runtime_files(tmp_path):
    with (
        patch("app.doctor.shutil.which", return_value="/available"),
        patch("app.doctor.runtime_root", return_value=tmp_path / "missing"),
    ):
        report = inspect_environment()
    assert report["status"] == "warning"
    assert not list(tmp_path.iterdir())


def test_invalid_toml_never_echoes_input(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text('api_key = "DO_NOT_DISPLAY_THIS_SECRET', encoding="utf-8")
    with patch("app.doctor.shutil.which", return_value="/available"):
        report = inspect_environment(config)
    assert report["status"] == "error"
    assert "DO_NOT_DISPLAY" not in json.dumps(report)


def test_non_loopback_binding_requires_attention(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text('listen_host = "0.0.0.0"\n[app]\napi_key = ""\n')
    with patch("app.doctor.shutil.which", return_value="/available"):
        report = inspect_environment(config)
    assert report["status"] == "warning"
    config.write_text('listen_host = "0.0.0.0"\n[app]\napi_key = "PRIVATE_TEST_VALUE"\n')
    with patch("app.doctor.shutil.which", return_value="/available"):
        report = inspect_environment(config)
    assert report["status"] == "ok"
    assert "PRIVATE_TEST_VALUE" not in json.dumps(report)


def test_missing_media_tool_is_error(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text('listen_host = "127.0.0.1"\n')
    with patch("app.doctor.shutil.which", return_value=None):
        assert inspect_environment(config)["status"] == "error"


def test_launcher_doctor_does_not_import_config_or_call_network(tmp_path):
    code = """
import sys, socket
def blocked(*args, **kwargs):
    raise AssertionError('Network access forbidden')
socket.socket = blocked
from app.launcher import main
result = main(['doctor', '--json'])
assert 'app.config.config' not in sys.modules
assert 'app.config' not in sys.modules
raise SystemExit(result)
"""
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True,
        env={**os.environ, "MPT_HOME": str(tmp_path)}, timeout=15,
    )
    # Tools may be absent on a test runner; that is a legitimate error exit.
    assert result.returncode in (0, 1), result.stderr
    report = json.loads(result.stdout)
    assert report["offline"] is True
    assert not list(tmp_path.iterdir())


def test_malformed_app_table_is_a_reported_error(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text('app = "unexpected"\n')
    with patch("app.doctor.shutil.which", return_value="/available"):
        assert inspect_environment(config)["status"] == "error"


def test_container_publication_requires_manual_opt_in():
    import yaml

    workflow = yaml.load(
        (ROOT / ".github/workflows/docker-ghcr.yml").read_text(),
        Loader=yaml.BaseLoader,
    )
    assert set(workflow["on"]) == {"workflow_dispatch"}
    assert workflow["on"]["workflow_dispatch"]["inputs"]["publish"]["default"] == "false"
    steps = workflow["jobs"]["publish"]["steps"]
    build = next(s for s in steps if s.get("uses", "").startswith("docker/build-push-action@"))
    assert build["with"]["push"] == "${{ inputs.publish }}"
    login = next(s for s in steps if s.get("uses", "").startswith("docker/login-action@"))
    assert login["if"] == "inputs.publish"
    assert workflow["env"]["IMAGE_NAME"] == "ghcr.io/${{ github.repository }}"
    assert workflow["permissions"] == {"contents": "read"}


def test_ci_has_read_only_repository_permissions():
    import yaml

    workflow = yaml.load(
        (ROOT / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader,
    )
    assert workflow["permissions"] == {"contents": "read"}
    assert all("permissions" not in job for job in workflow["jobs"].values())


def test_explicit_missing_config_is_error(tmp_path):
    with patch("app.doctor.shutil.which", return_value="/available"):
        report = inspect_environment(tmp_path / "wrong-name.toml")
    assert report["status"] == "error"


def test_invalid_binding_and_key_types_are_reported_without_values(tmp_path):
    config = tmp_path / "config.toml"
    for value in (
        'listen_host = 123\n',
        'listen_host = " "\n',
        'listen_host = ["PRIVATE_HOST"]\n',
        'listen_host = "127.0.0.1"\n[app]\napi_key = 42\n',
        'listen_host = "127.0.0.1"\n[app]\napi_key = ["PRIVATE_VALUE"]\n',
    ):
        config.write_text(value)
        with patch("app.doctor.shutil.which", return_value="/available"):
            report = inspect_environment(config)
        assert report["status"] == "error"
        assert "PRIVATE" not in json.dumps(report)


def test_explicit_missing_config_cli_exits_one_without_path(capsys, tmp_path):
    from app.doctor import main

    with patch("app.doctor.shutil.which", return_value="/available"):
        result = main(["--config", str(tmp_path / "PRIVATE_PATH.toml"), "--json"])
    assert result == 1
    output = capsys.readouterr().out
    assert "PRIVATE_PATH" not in output
    assert json.loads(output)["status"] == "error"
