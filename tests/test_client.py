"""Unit tests for OpenRouterClient (mocked HTTP)."""

import base64
from unittest.mock import MagicMock, patch, mock_open

import pytest
import requests

from mcp_openrouter.client import OpenRouterClient


@pytest.fixture
def client():
    return OpenRouterClient("test-api-key")


class TestClientInit:
    def test_headers(self, client):
        assert client.headers["Authorization"] == "Bearer test-api-key"
        assert client.headers["Content-Type"] == "application/json"
        assert "HTTP-Referer" in client.headers
        assert "X-Title" in client.headers


class TestRequest:
    def test_get_success(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": []}
        with patch("requests.get", return_value=mock_resp):
            result = client._request("GET", "models")
        assert result == {"data": []}

    def test_post_success(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"choices": []}
        with patch("requests.post", return_value=mock_resp):
            result = client._request("POST", "chat/completions", {"model": "x"})
        assert result == {"choices": []}

    @pytest.mark.parametrize("code", [429, 502, 503, 408])
    def test_retries_on_retryable_then_succeeds(self, client, code):
        fail_resp = MagicMock()
        fail_resp.status_code = code
        fail_resp.json.return_value = {"error": {"code": code, "message": "err"}}

        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"ok": True}

        with patch("requests.post", side_effect=[fail_resp, ok_resp]), \
             patch("time.sleep"):
            result = client._request("POST", "endpoint", {}, max_retries=2)
        assert result == {"ok": True}

    @pytest.mark.parametrize("code", [400, 401, 402, 403])
    def test_non_retryable_raises_immediately(self, client, code):
        resp = MagicMock()
        resp.status_code = code
        resp.json.return_value = {"error": {"code": code, "message": "err"}}

        with patch("requests.post", return_value=resp):
            with pytest.raises(Exception, match=f"OpenRouter error {code}"):
                client._request("POST", "endpoint", {}, max_retries=3)

    def test_timeout_retries_then_raises(self, client):
        with patch("requests.post", side_effect=requests.exceptions.Timeout):
            with pytest.raises(Exception, match="timed out"):
                client._request("POST", "endpoint", {}, max_retries=2)

    def test_network_error_raises_immediately(self, client):
        with patch("requests.post", side_effect=requests.exceptions.ConnectionError("fail")):
            with pytest.raises(Exception, match="Network error"):
                client._request("POST", "endpoint", {})

    def test_max_retries_exceeded(self, client):
        resp = MagicMock()
        resp.status_code = 429
        resp.json.return_value = {"error": {"code": 429, "message": "rate limited"}}

        with patch("requests.post", return_value=resp), \
             patch("time.sleep"):
            with pytest.raises(Exception, match="429"):
                client._request("POST", "endpoint", {}, max_retries=3)


class TestChat:
    def test_builds_payload(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"choices": [{"message": {"content": "hi"}}]}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            client.chat("model/x", [{"role": "user", "content": "hello"}], temperature=0.5)
            payload = mock_post.call_args[1]["json"]
            assert payload["model"] == "model/x"
            assert payload["messages"] == [{"role": "user", "content": "hello"}]
            assert payload["temperature"] == 0.5


class TestChatSimple:
    def test_returns_content(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"choices": [{"message": {"content": "response"}}]}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = client.chat_simple("model/x", "hello")
            assert result == "response"
            payload = mock_post.call_args[1]["json"]
            assert payload["messages"] == [{"role": "user", "content": "hello"}]

    def test_with_system_prompt(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"choices": [{"message": {"content": "ok"}}]}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            client.chat_simple("model/x", "hello", system="be helpful")
            payload = mock_post.call_args[1]["json"]
            assert payload["messages"][0] == {"role": "system", "content": "be helpful"}
            assert payload["messages"][1] == {"role": "user", "content": "hello"}


class TestGenerateImage:
    def test_builds_payload(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"images": [
                {"image_url": {"url": "data:image/png;base64,AAAA"}}
            ]}}]
        }

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = client.generate_image("model/x", "a cat", background="transparent", quality="high", output_format="png")
            payload = mock_post.call_args[1]["json"]
            assert payload["model"] == "model/x"
            assert payload["modalities"] == ["image", "text"]
            assert payload["background"] == "transparent"
            assert payload["quality"] == "high"
            assert payload["output_format"] == "png"
            assert len(result) == 1

    def test_saves_to_file(self, client, tmp_path):
        img_data = base64.b64encode(b"fake-image").decode()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"images": [
                {"image_url": {"url": f"data:image/png;base64,{img_data}"}}
            ]}}]
        }

        out = tmp_path / "output.png"
        with patch("requests.post", return_value=mock_resp):
            client.generate_image("model/x", "a cat", output_path=str(out))
        assert out.read_bytes() == b"fake-image"

    def test_multiple_images(self, client, tmp_path):
        img_data = base64.b64encode(b"img").decode()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"images": [
                {"image_url": {"url": f"data:image/png;base64,{img_data}"}},
                {"image_url": {"url": f"data:image/png;base64,{img_data}"}},
            ]}}]
        }

        out = tmp_path / "output.png"
        with patch("requests.post", return_value=mock_resp):
            result = client.generate_image("model/x", "cats", output_path=str(out))
        assert len(result) == 2
        assert (tmp_path / "output_0.png").exists()
        assert (tmp_path / "output_1.png").exists()


class TestListModels:
    def test_returns_models(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": [
            {"slug": "a/b", "name": "B", "context_length": 4096,
             "input_modalities": ["text"], "output_modalities": ["text"],
             "supported_parameters": ["tools"]},
        ]}

        with patch("requests.get", return_value=mock_resp):
            result = client.list_models()
        assert len(result) == 1
        assert result[0]["slug"] == "a/b"

    def test_filter_vision(self, client):
        models = [
            {"slug": "a", "name": "A", "input_modalities": ["image", "text"], "output_modalities": ["text"], "supported_parameters": []},
            {"slug": "b", "name": "B", "input_modalities": ["text"], "output_modalities": ["text"], "supported_parameters": []},
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": models}

        with patch("requests.get", return_value=mock_resp):
            result = client.list_models("vision")
        assert len(result) == 1
        assert result[0]["slug"] == "a"

    def test_filter_image_gen(self, client):
        models = [
            {"slug": "a", "name": "A", "input_modalities": ["text"], "output_modalities": ["image"], "supported_parameters": []},
            {"slug": "b", "name": "B", "input_modalities": ["text"], "output_modalities": ["text"], "supported_parameters": []},
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": models}

        with patch("requests.get", return_value=mock_resp):
            result = client.list_models("image_gen")
        assert len(result) == 1

    def test_filter_tools(self, client):
        models = [
            {"slug": "a", "name": "A", "supported_parameters": ["tools"]},
            {"slug": "b", "name": "B", "supported_parameters": []},
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": models}

        with patch("requests.get", return_value=mock_resp):
            result = client.list_models("tools")
        assert len(result) == 1

    def test_filter_long_context(self, client):
        models = [
            {"slug": "a", "name": "A", "context_length": 200000},
            {"slug": "b", "name": "B", "context_length": 4096},
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": models}

        with patch("requests.get", return_value=mock_resp):
            result = client.list_models("long_context")
        assert len(result) == 1


class TestFindModel:
    def test_case_insensitive(self, client):
        models = [
            {"slug": "anthropic/Claude-Sonnet", "name": "Claude Sonnet"},
            {"slug": "openai/gpt-4", "name": "GPT-4"},
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": models}

        with patch("requests.get", return_value=mock_resp):
            result = client.find_model("claude")
        assert len(result) == 1
        assert result[0]["slug"] == "anthropic/Claude-Sonnet"

    def test_no_matches(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": [{"slug": "a/b", "name": "B"}]}

        with patch("requests.get", return_value=mock_resp):
            result = client.find_model("nonexistent")
        assert result == []
