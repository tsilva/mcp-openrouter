"""Unit tests for server tool functions (mocked client)."""

import base64
import os
from unittest.mock import MagicMock, patch

import pytest

from mcp_openrouter.server import chat as _chat_tool, generate_image as _gen_tool, embed as _embed_tool, list_models as _list_tool, find_models as _find_tool, get_client

# Unwrap FastMCP FunctionTool wrappers to get the raw functions
chat = _chat_tool.fn
generate_image = _gen_tool.fn
embed = _embed_tool.fn
list_models = _list_tool.fn
find_models = _find_tool.fn


def _mock_chat_response(content="response"):
    return {"choices": [{"message": {"content": content}}]}


def _make_image_response(fmt="png", data=b"fake"):
    b64 = base64.b64encode(data).decode()
    return {
        "choices": [{"message": {"images": [
            {"image_url": {"url": f"data:image/{fmt};base64,{b64}"}}
        ]}}]
    }


class TestGetClient:
    def test_raises_without_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                get_client()


class TestChatTool:
    @patch("mcp_openrouter.server.get_client")
    def test_prompt_builds_user_message(self, mock_gc):
        client = MagicMock()
        client.chat.return_value = _mock_chat_response("hi")
        mock_gc.return_value = client

        result = chat(prompt="hello", model="m/x")
        assert result == "hi"
        msgs = client.chat.call_args[0][1]
        assert msgs == [{"role": "user", "content": "hello"}]

    @patch("mcp_openrouter.server.get_client")
    def test_messages_pass_through(self, mock_gc):
        client = MagicMock()
        client.chat.return_value = _mock_chat_response()
        mock_gc.return_value = client

        conv = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hey"}]
        chat(messages=conv, model="m/x")
        msgs = client.chat.call_args[0][1]
        assert msgs == conv

    def test_raises_if_both_prompt_and_messages(self):
        with pytest.raises(ValueError, match="not both"):
            chat(prompt="hi", messages=[{"role": "user", "content": "hi"}], model="m/x")

    def test_raises_if_neither(self):
        with pytest.raises(ValueError, match="must be provided"):
            chat(model="m/x")

    def test_raises_if_no_model_and_no_default(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="No model"):
                chat(prompt="hi")

    @patch("mcp_openrouter.server.get_client")
    def test_system_prompt_prepended(self, mock_gc):
        client = MagicMock()
        client.chat.return_value = _mock_chat_response()
        mock_gc.return_value = client

        chat(prompt="hi", model="m/x", system="be nice")
        msgs = client.chat.call_args[0][1]
        assert msgs[0] == {"role": "system", "content": "be nice"}
        assert msgs[1] == {"role": "user", "content": "hi"}

    @patch("mcp_openrouter.server.get_client")
    def test_assistant_prefill_appended(self, mock_gc):
        client = MagicMock()
        client.chat.return_value = _mock_chat_response()
        mock_gc.return_value = client

        chat(prompt="hi", model="m/x", assistant_prefill="Sure,")
        msgs = client.chat.call_args[0][1]
        assert msgs[-1] == {"role": "assistant", "content": "Sure,"}

    @patch("mcp_openrouter.server.get_client")
    def test_kwargs_forwarded(self, mock_gc):
        client = MagicMock()
        client.chat.return_value = _mock_chat_response()
        mock_gc.return_value = client

        chat(prompt="hi", model="m/x", temperature=0.5, max_tokens=100, top_p=0.9,
             top_k=50, frequency_penalty=0.1, presence_penalty=0.2, seed=42,
             stop=["END"])
        kwargs = client.chat.call_args[1]
        assert kwargs["temperature"] == 0.5
        assert kwargs["max_tokens"] == 100
        assert kwargs["seed"] == 42
        assert kwargs["stop"] == ["END"]

    @patch("mcp_openrouter.server.get_client")
    def test_json_mode(self, mock_gc):
        client = MagicMock()
        client.chat.return_value = _mock_chat_response()
        mock_gc.return_value = client

        chat(prompt="hi", model="m/x", json_mode=True)
        kwargs = client.chat.call_args[1]
        assert kwargs["response_format"] == {"type": "json_object"}

    @patch("mcp_openrouter.server.get_client")
    def test_response_format_overrides_json_mode(self, mock_gc):
        client = MagicMock()
        client.chat.return_value = _mock_chat_response()
        mock_gc.return_value = client

        fmt = {"type": "json_schema", "schema": {}}
        chat(prompt="hi", model="m/x", json_mode=True, response_format=fmt)
        kwargs = client.chat.call_args[1]
        assert kwargs["response_format"] == fmt

    @patch("mcp_openrouter.server.get_client")
    def test_reasoning_effort(self, mock_gc):
        client = MagicMock()
        client.chat.return_value = _mock_chat_response()
        mock_gc.return_value = client

        chat(prompt="hi", model="m/x", reasoning_effort="high")
        kwargs = client.chat.call_args[1]
        assert kwargs["reasoning"] == {"effort": "high"}

    @patch("mcp_openrouter.server.get_client")
    @patch.dict(os.environ, {"DEFAULT_TEXT_MODEL": "default/model"})
    def test_uses_default_model(self, mock_gc):
        client = MagicMock()
        client.chat.return_value = _mock_chat_response()
        mock_gc.return_value = client

        chat(prompt="hi")
        assert client.chat.call_args[0][0] == "default/model"


class TestGenerateImageTool:
    def test_raises_without_model_or_default(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="No model"):
                generate_image(prompt="a cat")

    @patch("mcp_openrouter.server.get_client")
    def test_raises_on_relative_output_path(self, mock_gc):
        client = MagicMock()
        client.generate_image.return_value = [
            {"image_url": {"url": "data:image/png;base64," + base64.b64encode(b"x").decode()}}
        ]
        mock_gc.return_value = client

        with pytest.raises(ValueError, match="absolute path"):
            generate_image(prompt="a cat", model="m/x", output_path="relative/path.png")

    @patch("mcp_openrouter.server.get_client")
    def test_returns_image(self, mock_gc):
        b64 = base64.b64encode(b"imgdata").decode()
        client = MagicMock()
        client.generate_image.return_value = [
            {"image_url": {"url": f"data:image/webp;base64,{b64}"}}
        ]
        mock_gc.return_value = client

        result = generate_image(prompt="a cat", model="m/x")
        # Image is a fastmcp type; verify it was created (it's an Image instance)
        from fastmcp.utilities.types import Image as ImageType
        assert isinstance(result, ImageType)

    @patch("mcp_openrouter.server.get_client")
    def test_saves_file(self, mock_gc, tmp_path):
        b64 = base64.b64encode(b"imgdata").decode()
        client = MagicMock()
        client.generate_image.return_value = [
            {"image_url": {"url": f"data:image/png;base64,{b64}"}}
        ]
        mock_gc.return_value = client

        out = tmp_path / "out.png"
        generate_image(prompt="a cat", model="m/x", output_path=str(out))
        assert out.read_bytes() == b"imgdata"

    @patch("mcp_openrouter.server.get_client")
    def test_raises_when_no_images(self, mock_gc):
        client = MagicMock()
        client.generate_image.return_value = []
        mock_gc.return_value = client

        with pytest.raises(ValueError, match="No image"):
            generate_image(prompt="a cat", model="m/x")


class TestEmbedTool:
    def test_raises_without_model_or_default(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="No model"):
                embed(input="hello")

    @patch("mcp_openrouter.server.get_client")
    def test_string_input(self, mock_gc):
        client = MagicMock()
        client.embeddings.return_value = {
            "data": [{"object": "embedding", "embedding": [0.1, 0.2], "index": 0}],
            "model": "m/x",
            "usage": {"prompt_tokens": 5, "total_tokens": 5},
        }
        mock_gc.return_value = client

        result = embed(input="hello", model="m/x")
        client.embeddings.assert_called_once_with("m/x", "hello")
        assert result["data"][0]["embedding"] == [0.1, 0.2]

    @patch("mcp_openrouter.server.get_client")
    def test_list_input(self, mock_gc):
        client = MagicMock()
        client.embeddings.return_value = {
            "data": [
                {"object": "embedding", "embedding": [0.1], "index": 0},
                {"object": "embedding", "embedding": [0.2], "index": 1},
            ],
            "model": "m/x",
            "usage": {"prompt_tokens": 10, "total_tokens": 10},
        }
        mock_gc.return_value = client

        result = embed(input=["hello", "world"], model="m/x")
        client.embeddings.assert_called_once_with("m/x", ["hello", "world"])
        assert len(result["data"]) == 2

    @patch("mcp_openrouter.server.get_client")
    def test_optional_params_forwarded(self, mock_gc):
        client = MagicMock()
        client.embeddings.return_value = {"data": [], "model": "m/x", "usage": {}}
        mock_gc.return_value = client

        embed(input="hello", model="m/x", encoding_format="base64", dimensions=512)
        client.embeddings.assert_called_once_with(
            "m/x", "hello", encoding_format="base64", dimensions=512
        )

    @patch("mcp_openrouter.server.get_client")
    @patch.dict(os.environ, {"DEFAULT_EMBEDDING_MODEL": "default/embed"})
    def test_uses_default_model(self, mock_gc):
        client = MagicMock()
        client.embeddings.return_value = {"data": [], "model": "default/embed", "usage": {}}
        mock_gc.return_value = client

        embed(input="hello")
        assert client.embeddings.call_args[0][0] == "default/embed"

    @patch("mcp_openrouter.server.get_client")
    def test_omits_none_params(self, mock_gc):
        client = MagicMock()
        client.embeddings.return_value = {"data": [], "model": "m/x", "usage": {}}
        mock_gc.return_value = client

        embed(input="hello", model="m/x")
        # Should only pass model and input, no extra kwargs
        client.embeddings.assert_called_once_with("m/x", "hello")


class TestListModelsTool:
    @patch("mcp_openrouter.server.get_client")
    def test_returns_simplified(self, mock_gc):
        client = MagicMock()
        client.list_models.return_value = [
            {"slug": "a/b", "name": "B", "context_length": 4096,
             "pricing": {"prompt": "0.01", "completion": "0.02"}},
        ]
        mock_gc.return_value = client

        result = list_models()
        assert len(result) == 1
        assert result[0]["slug"] == "a/b"
        assert result[0]["pricing"]["prompt"] == "0.01"


class TestFindModelsTool:
    @patch("mcp_openrouter.server.get_client")
    def test_returns_max_20(self, mock_gc):
        client = MagicMock()
        client.find_model.return_value = [
            {"slug": f"m/{i}", "name": f"M{i}", "context_length": 4096}
            for i in range(30)
        ]
        mock_gc.return_value = client

        result = find_models("m")
        assert len(result) == 20

    @patch("mcp_openrouter.server.get_client")
    def test_simplified_format(self, mock_gc):
        client = MagicMock()
        client.find_model.return_value = [
            {"slug": "a/b", "name": "B", "context_length": 4096, "extra": "stuff"},
        ]
        mock_gc.return_value = client

        result = find_models("b")
        assert set(result[0].keys()) == {"slug", "name", "context_length"}
