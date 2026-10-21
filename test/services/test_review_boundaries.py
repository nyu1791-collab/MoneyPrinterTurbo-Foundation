"""Offline regressions reproduced during the whole-repository review."""
from unittest.mock import patch

import pytest

from app.services import kimi_code_oauth as oauth
from app.services import subtitle


class ProviderResponse:
    def __init__(self, payload, status=200, invalid_json=False):
        self.payload = payload
        self.status_code = status
        self.invalid_json = invalid_json
        self.text = "PRIVATE_RAW_RESPONSE"

    def json(self):
        if self.invalid_json:
            raise ValueError("PRIVATE_PARSER_DETAIL")
        return self.payload


def invoke_oauth(operation):
    if operation == "device":
        return oauth.request_device_code("china")
    if operation == "poll":
        return oauth.poll_token("china", "TEST_DEVICE")
    return oauth._refresh("china", "TEST_REFRESH")


def test_subtitle_similarity_accepts_empty_inputs():
    assert subtitle.similarity("", "") == 1.0
    assert subtitle.similarity("", "a") == 0.0
    assert subtitle.similarity("a", "") == 0.0


@pytest.mark.parametrize("operation", ["device", "poll", "refresh"])
@pytest.mark.parametrize("payload", [[], None, "PRIVATE_STRING", 123, True])
def test_oauth_rejects_non_object_json_as_safe_value_error(operation, payload):
    with (
        patch.object(oauth, "_identity_headers", return_value={}),
        patch.object(oauth.requests, "post", return_value=ProviderResponse(payload)),
        pytest.raises(ValueError) as caught,
    ):
        invoke_oauth(operation)
    assert "JSON object" in str(caught.value)
    assert "PRIVATE" not in str(caught.value)


@pytest.mark.parametrize("operation", ["device", "poll", "refresh"])
@pytest.mark.parametrize("invalid_json", [False, True])
def test_oauth_errors_omit_provider_bodies_and_descriptions(operation, invalid_json):
    response = ProviderResponse(
        {"error": "PRIVATE_ERROR", "error_description": "PRIVATE_DESCRIPTION",
         "refresh_token": "PRIVATE_TOKEN"},
        status=400 if operation == "device" else 200,
        invalid_json=invalid_json,
    )
    with (
        patch.object(oauth, "_identity_headers", return_value={}),
        patch.object(oauth.requests, "post", return_value=response),
        pytest.raises(ValueError) as caught,
    ):
        invoke_oauth(operation)
    assert "PRIVATE" not in str(caught.value)
    assert "HTTP" in str(caught.value)


@pytest.mark.parametrize("operation", ["device", "poll", "refresh"])
def test_oauth_errors_keep_standard_error_identifier_only(operation):
    response = ProviderResponse(
        {"error": "invalid_grant", "error_description": "PRIVATE_DESCRIPTION"},
        status=400 if operation == "device" else 200,
    )
    with (
        patch.object(oauth, "_identity_headers", return_value={}),
        patch.object(oauth.requests, "post", return_value=response),
        pytest.raises(ValueError) as caught,
    ):
        invoke_oauth(operation)
    message = str(caught.value)
    assert "error=invalid_grant" in message
    assert "HTTP" in message
    assert "PRIVATE" not in message


@pytest.mark.parametrize("operation", ["device", "poll", "refresh"])
def test_oauth_unknown_error_identifier_is_not_echoed(operation):
    response = ProviderResponse(
        {"error": "PRIVATE_ERROR_CODE"},
        status=400 if operation == "device" else 200,
    )
    with (
        patch.object(oauth, "_identity_headers", return_value={}),
        patch.object(oauth.requests, "post", return_value=response),
        pytest.raises(ValueError) as caught,
    ):
        invoke_oauth(operation)
    assert "error=" not in str(caught.value)
    assert "PRIVATE" not in str(caught.value)
