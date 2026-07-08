"""Unit tests for the ConversationRepresentation layer."""

from __future__ import annotations

import json

from conversation.models import Conversation, Message, MessageRole, ToolCall
from llm.conversation_representation import (
    ConversationRepresentation,
    DeepSeekConversationRepresentation,
)


class TestDeepSeekConversationRepresentation:
    """Tests for :class:`DeepSeekConversationRepresentation`."""

    def setup_method(self) -> None:
        self.representation = DeepSeekConversationRepresentation()

    def test_is_conversation_representation(self) -> None:
        assert isinstance(
            self.representation, ConversationRepresentation
        )

    def test_empty_conversation(self) -> None:
        conv = Conversation()
        result = self.representation.to_provider_messages(conv)
        assert result == []

    def test_user_message(self) -> None:
        conv = Conversation().add_user_message("hello")
        result = self.representation.to_provider_messages(conv)
        assert result == [{"role": "user", "content": "hello"}]

    def test_assistant_message_with_content(self) -> None:
        conv = Conversation().add_assistant_message(content="reply")
        result = self.representation.to_provider_messages(conv)
        assert result == [{"role": "assistant", "content": "reply"}]

    def test_assistant_message_with_tool_calls(self) -> None:
        tcs = [ToolCall(id="c1", name="read_file", arguments={"path": "x"})]
        conv = Conversation().add_assistant_message(tool_calls=tcs)
        result = self.representation.to_provider_messages(conv)

        assert len(result) == 1
        assert result[0]["role"] == "assistant"
        assert result[0]["content"] is None
        assert "tool_calls" in result[0]
        assert len(result[0]["tool_calls"]) == 1
        assert result[0]["tool_calls"][0] == {
            "id": "c1",
            "type": "function",
            "function": {
                "name": "read_file",
                "arguments": json.dumps({"path": "x"}),
            },
        }

    def test_assistant_message_with_content_and_tool_calls(self) -> None:
        tcs = [ToolCall(id="c1", name="echo", arguments={"k": "v"})]
        conv = Conversation().add_assistant_message(
            content="thinking…", tool_calls=tcs
        )
        result = self.representation.to_provider_messages(conv)

        assert result[0]["role"] == "assistant"
        assert result[0]["content"] == "thinking…"
        assert len(result[0]["tool_calls"]) == 1

    def test_tool_message(self) -> None:
        conv = Conversation().add_tool_message(
            tool_call_id="call_1", content="tool output"
        )
        result = self.representation.to_provider_messages(conv)

        assert result == [
            {
                "role": "tool",
                "content": "tool output",
                "tool_call_id": "call_1",
            }
        ]

    def test_full_conversation_roundtrip(self) -> None:
        """Verify a multi-message conversation translates correctly."""
        conv = (
            Conversation()
            .add_user_message("read the file")
            .add_assistant_message(
                tool_calls=[
                    ToolCall(id="c1", name="read_file", arguments={"path": "x"})
                ]
            )
            .add_tool_message(tool_call_id="c1", content="file contents")
            .add_assistant_message(content="the file says: …")
        )

        result = self.representation.to_provider_messages(conv)

        assert len(result) == 4
        assert result[0] == {"role": "user", "content": "read the file"}
        assert result[1]["role"] == "assistant"
        assert len(result[1]["tool_calls"]) == 1
        assert result[2] == {
            "role": "tool",
            "content": "file contents",
            "tool_call_id": "c1",
        }
        assert result[3] == {"role": "assistant", "content": "the file says: …"}

    def test_is_stateless(self) -> None:
        """Repeated calls with the same input must produce identical output."""
        conv = Conversation().add_user_message("test")
        first = self.representation.to_provider_messages(conv)
        second = self.representation.to_provider_messages(conv)
        assert first == second

    def test_multiple_tool_calls_in_one_message(self) -> None:
        tcs = [
            ToolCall(id="c1", name="tool_a", arguments={}),
            ToolCall(id="c2", name="tool_b", arguments={"x": 1}),
        ]
        conv = Conversation().add_assistant_message(tool_calls=tcs)
        result = self.representation.to_provider_messages(conv)

        assert len(result[0]["tool_calls"]) == 2
        assert result[0]["tool_calls"][0]["id"] == "c1"
        assert result[0]["tool_calls"][1]["id"] == "c2"

    def test_user_message_with_empty_content(self) -> None:
        conv = Conversation().add_user_message("")
        result = self.representation.to_provider_messages(conv)
        assert result == [{"role": "user", "content": ""}]