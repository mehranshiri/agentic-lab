"""Unit tests for the Conversation domain models."""

from __future__ import annotations

import pytest

from conversation.models import (
    Conversation,
    Message,
    MessageRole,
    ToolCall,
)


# ---------------------------------------------------------------------------
# MessageRole
# ---------------------------------------------------------------------------


class TestMessageRole:
    """Tests for :class:`MessageRole` enum."""

    def test_user_role(self) -> None:
        assert MessageRole.USER.value == "user"

    def test_assistant_role(self) -> None:
        assert MessageRole.ASSISTANT.value == "assistant"

    def test_tool_role(self) -> None:
        assert MessageRole.TOOL.value == "tool"


# ---------------------------------------------------------------------------
# ToolCall
# ---------------------------------------------------------------------------


class TestToolCall:
    """Tests for :class:`ToolCall` value object."""

    def test_is_frozen(self) -> None:
        tc = ToolCall(id="call_1", name="read_file", arguments={"path": "x"})
        with pytest.raises(Exception):
            tc.name = "write_file"  # type: ignore[misc]

    def test_equality(self) -> None:
        a = ToolCall(id="1", name="t", arguments={"k": "v"})
        b = ToolCall(id="1", name="t", arguments={"k": "v"})
        assert a == b

    def test_inequality(self) -> None:
        a = ToolCall(id="1", name="a", arguments={})
        b = ToolCall(id="2", name="b", arguments={})
        assert a != b

    def test_empty_arguments(self) -> None:
        tc = ToolCall(id="call_1", name="no_args", arguments={})
        assert tc.arguments == {}


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------


class TestMessage:
    """Tests for :class:`Message` value object."""

    def test_is_frozen(self) -> None:
        msg = Message(role=MessageRole.USER, content="hello")
        with pytest.raises(Exception):
            msg.content = "bye"  # type: ignore[misc]

    def test_user_message(self) -> None:
        msg = Message(role=MessageRole.USER, content="prompt")
        assert msg.role == MessageRole.USER
        assert msg.content == "prompt"
        assert msg.tool_call_id is None
        assert msg.tool_calls is None

    def test_assistant_message_with_content(self) -> None:
        msg = Message(role=MessageRole.ASSISTANT, content="reply")
        assert msg.role == MessageRole.ASSISTANT
        assert msg.content == "reply"

    def test_assistant_message_with_tool_calls(self) -> None:
        tcs = [ToolCall(id="c1", name="echo", arguments={})]
        msg = Message(
            role=MessageRole.ASSISTANT, content=None, tool_calls=tcs
        )
        assert msg.content is None
        assert msg.tool_calls == tcs

    def test_assistant_message_with_both(self) -> None:
        tcs = [ToolCall(id="c1", name="echo", arguments={})]
        msg = Message(
            role=MessageRole.ASSISTANT,
            content="thinking…",
            tool_calls=tcs,
        )
        assert msg.content == "thinking…"
        assert msg.tool_calls == tcs

    def test_tool_message(self) -> None:
        msg = Message(
            role=MessageRole.TOOL,
            content="result text",
            tool_call_id="call_1",
        )
        assert msg.role == MessageRole.TOOL
        assert msg.content == "result text"
        assert msg.tool_call_id == "call_1"

    def test_tool_message_requires_tool_call_id(self) -> None:
        with pytest.raises(ValueError, match="tool_call_id"):
            Message(role=MessageRole.TOOL, content="oops")

    def test_tool_message_equality(self) -> None:
        a = Message(role=MessageRole.TOOL, content="x", tool_call_id="1")
        b = Message(role=MessageRole.TOOL, content="x", tool_call_id="1")
        assert a == b


# ---------------------------------------------------------------------------
# Conversation
# ---------------------------------------------------------------------------


class TestConversation:
    """Tests for :class:`Conversation` immutable collection."""

    def test_is_frozen(self) -> None:
        conv = Conversation()
        with pytest.raises(Exception):
            conv.messages = []  # type: ignore[misc]

    def test_empty_conversation(self) -> None:
        conv = Conversation()
        assert len(conv) == 0
        assert conv.messages == []

    def test_add_user_message_returns_new_instance(self) -> None:
        conv = Conversation()
        conv2 = conv.add_user_message("hello")
        assert conv is not conv2
        assert len(conv) == 0
        assert len(conv2) == 1
        assert conv2.messages[0].role == MessageRole.USER
        assert conv2.messages[0].content == "hello"

    def test_add_assistant_message_returns_new_instance(self) -> None:
        conv = Conversation()
        conv2 = conv.add_assistant_message(content="reply")
        assert conv is not conv2
        assert conv2.messages[0].role == MessageRole.ASSISTANT
        assert conv2.messages[0].content == "reply"

    def test_add_assistant_message_with_tool_calls(self) -> None:
        tcs = [ToolCall(id="c1", name="echo", arguments={})]
        conv = Conversation().add_assistant_message(tool_calls=tcs)
        assert conv.messages[0].tool_calls == tcs

    def test_add_tool_message_returns_new_instance(self) -> None:
        conv = Conversation()
        conv2 = conv.add_tool_message(
            tool_call_id="call_1", content="result"
        )
        assert conv is not conv2
        assert conv2.messages[0].role == MessageRole.TOOL
        assert conv2.messages[0].tool_call_id == "call_1"
        assert conv2.messages[0].content == "result"

    def test_full_conversation_flow(self) -> None:
        """End-to-end: user → assistant (tool_call) → tool → assistant."""
        conv = Conversation()
        conv = conv.add_user_message("read the file")
        conv = conv.add_assistant_message(
            tool_calls=[ToolCall(id="c1", name="read_file", arguments={"path": "x"})]
        )
        conv = conv.add_tool_message(tool_call_id="c1", content="file contents")
        conv = conv.add_assistant_message(content="the file says: …")

        assert len(conv) == 4
        assert conv.messages[0].role == MessageRole.USER
        assert conv.messages[1].role == MessageRole.ASSISTANT
        assert conv.messages[1].tool_calls is not None
        assert conv.messages[2].role == MessageRole.TOOL
        assert conv.messages[3].role == MessageRole.ASSISTANT
        assert conv.messages[3].content == "the file says: …"

    def test_immutability_across_mutations(self) -> None:
        """Every mutation must produce a new, independent instance."""
        conv1 = Conversation()
        conv2 = conv1.add_user_message("step 1")
        conv3 = conv2.add_assistant_message(content="step 2")

        assert len(conv1) == 0
        assert len(conv2) == 1
        assert len(conv3) == 2

    def test_multiple_user_messages(self) -> None:
        conv = (
            Conversation()
            .add_user_message("first")
            .add_assistant_message(content="a")
            .add_user_message("second")
        )
        assert len(conv) == 3
        assert conv.messages[0].content == "first"
        assert conv.messages[2].content == "second"