from unittest.mock import patch

import httpx
from openai import OpenAI
import toml

from app.config import config
from app.services import llm
from tools.use_youtube_en import apply_preset


def test_rate_limit_is_one_actual_http_request_without_sdk_or_outer_retry():
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(429, json={"error": {"message": "fixture quota", "type": "rate_limit"}})

    transport = httpx.Client(transport=httpx.MockTransport(respond))

    def client(**kwargs):
        return OpenAI(**kwargs, http_client=transport)

    with patch.dict(config.app, {"llm_provider": "openai", "openai_api_key": "fixture-key",
                                 "openai_model_name": "fixture-model",
                                 "openai_base_url": "https://fixture.invalid/v1"}, clear=True), \
            patch.object(llm, "OpenAI", side_effect=client):
        assert llm.generate_script("Coffee", language="en-US") == ""
    assert len(calls) == 1
    assert transport.is_closed


def test_paragraph_target_does_not_truncate_or_regenerate_valid_narration():
    with patch.object(llm, "_generate_response", return_value="One idea.\n\nA useful example.") as provider:
        result = llm.generate_script("日本語で書いたテーマ", language="en-US", paragraph_number=1)
    assert result == "One idea.\n\nA useful example."
    assert provider.call_count == 1
    assert "- language: en-US" in provider.call_args.args[0]
    assert "paragraph count is advisory" in provider.call_args.args[0]
    assert provider.call_args.kwargs["max_retries"] == 0


def test_english_preset_retains_credentials_and_later_user_edits(tmp_path):
    destination = tmp_path / "config.toml"
    destination.write_text(toml.dumps({"app": {"llm_provider": "chosen-provider",
                                               "openai_api_key": "fixture-key"},
                                       "ui": {"unrelated_setting": "keep"}}), encoding="utf-8")
    apply_preset(destination)
    current = toml.loads(destination.read_text(encoding="utf-8"))
    assert current["app"]["llm_provider"] == "chosen-provider"
    assert current["app"]["openai_api_key"] == "fixture-key"
    assert current["ui"]["unrelated_setting"] == "keep"
    assert current["ui"]["video_language"] == "en-US"
    current["ui"]["video_script_prompt"] = "My longer explainer target"
    destination.write_text(toml.dumps(current), encoding="utf-8")
    before = destination.read_bytes()
    apply_preset(destination)
    assert destination.read_bytes() == before
