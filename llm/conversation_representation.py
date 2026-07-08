"""Conversation Representation — translates domain Conversations into provider messages.

This module defines the abstraction and concrete implementations responsible
for converting a provider-independent :class:`~conversation.models.Conversation`
into the message format required by a specific LLM provider.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from conversation.models import Conversation, Message, MessageRole


class ConversationRepresentation(ABC):
    """Abstract strategy for translating a Conversation into provider messages.

    Responsibilities:
    * Accept a provider-independent :class:`~conversation.models.Conversation`.
    * Convert it into a list of provider-compatible message dicts.
    * Keep all provider-specific formatting inside the LLM module.

    The Conversation domain must never know how providers represent messages.
    """

    @abstractmethod
    def to_provider_messages(
        self, conversation: Conversation
    ) -> list[dict[str, Any]]:
        """Convert *conversation* into provider-compatible message dicts.

        Parameters
        ----------
        conversation:
            The provider-independent conversation to translate.

        Returns
        -------
        list[dict[str, Any]]
            A list of message dicts suitable for the provider's API.
        """
        ...


class DeepSeekConversationRepresentation(ConversationRepresentation):
    """Translate a Conversation into DeepSeek-compatible message dicts.

    DeepSeek's Chat Completions API follows the OpenAI convention:

    * User messages: ``{"role": "user", "content": "..."}``
    * Assistant messages with content:
      ``{"role": "assistant", "content": "..."}``
    * Assistant messages with tool calls:
      ``{"role": "assistant", "content": null, "tool_calls": [...]}``
    * Tool result messages:
      ``{"role": "tool", "content": "...", "tool_call_id": "..."}``
    """

    def to_provider_messages(
        self, conversation: Conversation
    ) -> list[dict[str, Any]]:
        """Convert *conversation* into DeepSeek-compatible message dicts.

        Parameters
        ----------
        conversation:
            The provider-independent conversation to translate.

        Returns
        -------
        list[dict[str, Any]]
            A list of message dicts suitable for DeepSeek's API.
        """
        messages: list[dict[str, Any]] = []

        for msg in conversation.messages:
            messages.append(self._convert_one(msg))

        return messages

    def _convert_one(self, message: Message) -> dict[str, Any]:
        """Convert a single domain Message into a DeepSeek-compatible dict.

        Parameters
        ----------
        message:
            The domain message to convert.

        Returns
        -------
        dict[str, Any]
            A DeepSeek-compatible message dict.
        """
        if message.role == MessageRole.USER:
            return {"role": "user", "content": message.content or ""}

        elif message.role == MessageRole.ASSISTANT:
            msg: dict[str, Any] = {"role": "assistant"}

            if message.tool_calls:
                msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in message.tool_calls
                ]

            # content can be null when there are only tool calls
            msg["content"] = message.content

            return msg

        elif message.role == MessageRole.TOOL:
            return {
                "role": "tool",
                "content": message.content or "",
                "tool_call_id": message.tool_call_id or "",
            }

        else:
            raise ValueError(f"Unknown message role: {message.role}")