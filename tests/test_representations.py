"""Unit tests for the provider tool-schema adapter layer."""

from __future__ import annotations

import pytest

from llm.representations.base import ToolSchemaAdapter
from llm.representations.deepseek import DeepSeekToolSchemaAdapter
from tools.metadata import ToolMetadata


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------


@pytest.fixture
def read_file_metadata() -> ToolMetadata:
    """Metadata matching the real ``ReadFileTool``."""
    return ToolMetadata(
        name="read_file",
        description="Read the contents of a text file. Does not modify the file.",
    )


@pytest.fixture
def dummy_metadata() -> ToolMetadata:
    """Generic tool metadata for edge-case testing."""
    return ToolMetadata(name="dummy_tool", description="A tool for testing.")


# ---------------------------------------------------------------------------
# DeepSeekToolSchemaAdapter
# ---------------------------------------------------------------------------


class TestDeepSeekToolSchemaAdapter:
    """Tests for :class:`DeepSeekToolSchemaAdapter`."""

    def test_is_tool_schema_adapter(self) -> None:
        """It should be a subclass of ``ToolSchemaAdapter``."""
        assert issubclass(DeepSeekToolSchemaAdapter, ToolSchemaAdapter)

    def test_produces_expected_top_level_keys(
        self, read_file_metadata: ToolMetadata
    ) -> None:
        """The returned dict must have 'type' and 'function' top-level keys."""
        adapter = DeepSeekToolSchemaAdapter()
        result = adapter.to_provider_format(read_file_metadata)

        assert "type" in result
        assert "function" in result

    def test_type_is_function(self, read_file_metadata: ToolMetadata) -> None:
        """The 'type' field must always be 'function'."""
        result = DeepSeekToolSchemaAdapter().to_provider_format(read_file_metadata)
        assert result["type"] == "function"

    def test_function_block_contains_name(
        self, read_file_metadata: ToolMetadata
    ) -> None:
        """The function block must include the tool name."""
        result = DeepSeekToolSchemaAdapter().to_provider_format(read_file_metadata)
        assert result["function"]["name"] == "read_file"

    def test_function_block_contains_description(
        self, read_file_metadata: ToolMetadata
    ) -> None:
        """The function block must include the tool description."""
        result = DeepSeekToolSchemaAdapter().to_provider_format(read_file_metadata)
        assert result["function"]["description"] == (
            "Read the contents of a text file. Does not modify the file."
        )

    def test_parameters_block_is_present_and_valid(
        self, read_file_metadata: ToolMetadata
    ) -> None:
        """The parameters block must have type, properties, and required keys."""
        result = DeepSeekToolSchemaAdapter().to_provider_format(read_file_metadata)
        params = result["function"]["parameters"]
        assert params["type"] == "object"
        assert isinstance(params["properties"], dict)
        assert isinstance(params["required"], list)

    def test_preserves_tool_name_from_metadata(
        self, dummy_metadata: ToolMetadata
    ) -> None:
        """The tool name in the output must match the input metadata."""
        result = DeepSeekToolSchemaAdapter().to_provider_format(dummy_metadata)
        assert result["function"]["name"] == "dummy_tool"

    def test_preserves_tool_description_from_metadata(
        self, dummy_metadata: ToolMetadata
    ) -> None:
        """The tool description in the output must match the input metadata."""
        result = DeepSeekToolSchemaAdapter().to_provider_format(dummy_metadata)
        assert result["function"]["description"] == "A tool for testing."

    def test_is_stateless(self, read_file_metadata: ToolMetadata) -> None:
        """Multiple calls with the same metadata must produce identical outputs."""
        adapter = DeepSeekToolSchemaAdapter()
        first = adapter.to_provider_format(read_file_metadata)
        second = adapter.to_provider_format(read_file_metadata)
        assert first == second


# ---------------------------------------------------------------------------
# ToolSchemaAdapter abstract base
# ---------------------------------------------------------------------------


class TestToolSchemaAdapterABC:
    """Tests for the ``ToolSchemaAdapter`` abstract base class."""

    def test_cannot_instantiate_abc(self) -> None:
        """``ToolSchemaAdapter`` must not be directly instantiable."""
        with pytest.raises(TypeError):
            ToolSchemaAdapter()  # type: ignore[abstract]

    def test_concrete_must_implement_to_provider_format(self) -> None:
        """Any concrete subclass must implement ``to_provider_format``."""
        # DeepSeekToolSchemaAdapter already does — verify it works
        adapter = DeepSeekToolSchemaAdapter()
        assert hasattr(adapter, "to_provider_format")
        metadata = ToolMetadata(name="test", description="desc")
        result = adapter.to_provider_format(metadata)
        assert isinstance(result, dict)
