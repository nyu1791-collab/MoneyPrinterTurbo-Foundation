"""Apply English production preferences without changing model credentials or publishing."""
from pathlib import Path
import os
import sys
import tempfile

import toml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.paths import config_template, runtime_root


def apply_preset(destination=None):
    destination = Path(destination) if destination else runtime_root() / "config.toml"
    source = destination if destination.is_file() else config_template()
    current = toml.loads(source.read_text(encoding="utf-8-sig"))
    if current.get("ui", {}).get("youtube_en_preset_version") == 1:
        return destination  # Preserve settings edited after the first launch.
    preset = toml.loads((ROOT / "presets/youtube-en.toml").read_text(encoding="utf-8"))
    for section, values in preset.items():
        current.setdefault(section, {}).update(values)
    current["ui"]["youtube_en_preset_version"] = 1
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n",
                                         dir=destination.parent, delete=False) as handle:
            temporary = Path(handle.name)
            toml.dump(current, handle)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return destination


if __name__ == "__main__":
    apply_preset()
    print("English explainer/trivia preferences applied. Model and API settings retained.")
