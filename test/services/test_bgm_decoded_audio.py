import io
import subprocess
import wave
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.services import bgm


def wav_bytes(frames):
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16000)
        audio.writeframes(b"\0\0" * frames)
    return output.getvalue()


def test_header_only_wav_rejected_by_real_ffmpeg(tmp_path):
    target = tmp_path / "empty.wav"
    target.write_bytes(wav_bytes(0))
    assert target.stat().st_size > 0
    with pytest.raises(bgm.BgmUploadError, match="audio"):
        bgm.validate_audio_file(str(target))


def test_empty_upload_rejected_and_staging_removed(tmp_path):
    with patch.object(bgm, "uploaded_bgm_dir", return_value=str(tmp_path)):
        with pytest.raises(bgm.BgmUploadError, match="audio"):
            bgm.save_bgm_upload("empty.wav", io.BytesIO(wav_bytes(0)))
    assert list(tmp_path.iterdir()) == []


def test_silence_with_positive_frames_remains_valid(tmp_path):
    target = tmp_path / "valid-silence.wav"
    target.write_bytes(wav_bytes(1600))
    bgm.validate_audio_file(str(target))


def test_damaged_mp3_rejected_even_when_ffmpeg_exits_zero(tmp_path):
    # Some FFmpeg builds return 0 after logging a damaged MP3 frame; the stderr error must reject it.
    complete = subprocess.run(
        [bgm.utils.get_ffmpeg_binary(), "-nostdin", "-v", "error", "-f", "lavfi",
         "-i", "sine=frequency=440:duration=2", "-f", "mp3", "-"],
        capture_output=True, check=True,
    ).stdout
    damaged = complete[:len(complete) * 2 // 5] + bytes(len(complete) // 5) + complete[len(complete) * 3 // 5:]
    target = tmp_path / "damaged.mp3"
    target.write_bytes(damaged)
    with pytest.raises(bgm.BgmUploadError, match="decodable"):
        bgm.validate_audio_file(str(target))


def test_stderr_error_rejects_when_ffmpeg_exits_zero(tmp_path):
    completed = SimpleNamespace(
        returncode=0,
        stdout=b"#tb 0: 1/16000\n0, 0, 0, 1, 2048, abc\n",
        stderr=b"[mp3float @ 0x1] Header missing\n",
    )
    with patch.object(bgm.subprocess, "run", return_value=completed):
        with pytest.raises(bgm.BgmUploadError, match="decodable"):
            bgm._validate_audio(str(tmp_path / "damaged.mp3"))


def test_decode_without_frames_is_rejected(tmp_path):
    completed = SimpleNamespace(returncode=0, stdout=b"#tb 0: 1/16000\n", stderr=b"")
    with patch.object(bgm.subprocess, "run", return_value=completed):
        with pytest.raises(bgm.BgmUploadError, match="nonempty"):
            bgm._validate_audio(str(tmp_path / "empty.wav"))
