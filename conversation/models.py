"""Provider-independent Conversation domain models.

Defines immutable value objects representing the complete interaction
history between a user, an assistant, and tool executions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MessageRole(Enum):
    """Roles supported in a Conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(frozen=True)
class ToolCall:
    """Provider-independent tool call within an assistant message.

    Attributes
    ----------
    id:
        Unique identifier for this tool call (provider-assigned).
    name:
        Name of the tool to invoke.
    arguments:
        Keyword arguments for the tool invocation.
    """

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class Message:
    """A single message in a Conversation.

    Supports all required message kinds:

    * **User** — ``role=USER``, ``content`` contains the prompt.
    * **Assistant** — ``role=ASSISTANT``.  May carry plain ``content``,
      ``tool_calls``, or both.
    * **Tool** — ``role=TOOL``.  Carries the result of a single tool
      execution identified by ``tool_call_id``.

    Attributes
    ----------
    role:
        Who produced this message (:class:`MessageRole`).
    content:
        Text content (user prompt, assistant reply, or tool output).
        May be ``None`` when the assistant only emits tool calls.
    tool_call_id:
        For tool messages, the id of the tool call this result fulfills.
    tool_calls:
        For assistant messages, the list of tool calls requested.
        Each element is a :class:`ToolCall`.
    """

    role: MessageRole
    content: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] | None = None

    def __post_init__(self) -> None:
        """Validate message consistency."""
        if self.role == MessageRole.TOOL and self.tool_call_id is None:
            raise ValueError(
                "Tool messages must have a 'tool_call_id'."
            )


@dataclass(frozen=True)
class Conversation:
    """Immutable, provider-independent conversation history.

    Every mutation returns a **new** :class:`Conversation` instance.
    The conversation is the single source of truth for an agent
    interaction and must never contain provider-specific details.

    Attributes
    ----------
    messages:
        Ordered list of :class:`Message` objects representing the full
        interaction history.
    """

    messages: list[Message] = field(default_factory=list)

    def add_user_message(self, content: str) -> Conversation:
        """Return a new Conversation with an appended user message.

        Parameters
        ----------
        content:
            The user's prompt text.

        Returns
        -------
        Conversation
            A new immutable instance containing the additional message.
        """
        message = Message(role=MessageRole.USER, content=content)
        return Conversation(messages=[*self.messages, message])

    def add_assistant_message(
        self,
        content: str | None = None,
        tool_calls: list[ToolCall] | None = None,
    ) -> Conversation:
        """Return a new Conversation with an appended assistant message.

        Parameters
        ----------
        content:
            Optional plain-text reply from the assistant.
        tool_calls:
            Optional list of tool calls the assistant requested.

        Returns
        -------
        Conversation
            A new immutable instance containing the additional message.
        """
        message = Message(
            role=MessageRole.ASSISTANT,
            content=content,
            tool_calls=tool_calls,
        )
        return Conversation(messages=[*self.messages, message])

    def add_tool_message(
        self, tool_call_id: str, content: str
    ) -> Conversation:
        """Return a new Conversation with an appended tool result message.

        Parameters
        ----------
        tool_call_id:
            The id of the tool call this result fulfills.
        content:
            The tool's output (success content or error text).

        Returns
        -------
        Conversation
            A new immutable instance containing the additional message.
        """
        message = Message(
            role=MessageRole.TOOL,
            content=content,
            tool_call_id=tool_call_id,
        )
        return Conversation(messages=[*self.messages, message])

    def __len__(self) -> int:
        return len(self.messages)