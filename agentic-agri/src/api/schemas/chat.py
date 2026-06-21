"""Chat domain DTOs — mirrors docs/chat-sse-be-spec.md §3."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MessageSender = Literal["user", "agent", "system", "action_prompt"]


class ExecutionTraceStep(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str
    description: str
    icon: str


class TableRow(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    region: str
    actual: str
    projected: str
    variance: str
    is_positive: bool = Field(alias="isPositive")


class AttachmentMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    file_name: str = Field(alias="fileName")
    mime_type: str = Field(alias="mimeType")
    size_bytes: int = Field(alias="sizeBytes")


class ActionButton(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    label: str
    icon: str
    action_id: str = Field(alias="actionId")


class AgentMessageData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    execution_trace: list[ExecutionTraceStep] | None = Field(
        default=None, alias="executionTrace"
    )
    paragraphs: list[str]
    table_header: str | None = Field(default=None, alias="tableHeader")
    table_rows: list[TableRow] | None = Field(default=None, alias="tableRows")
    action_buttons: list[ActionButton] | None = Field(
        default=None, alias="actionButtons"
    )


class ActionPromptOption(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    label: str
    action_id: str = Field(alias="actionId")


class ActionPromptData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str
    description: str
    options: list[ActionPromptOption]
    custom_option_label: str | None = Field(default=None, alias="customOptionLabel")


class Message(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    sender: MessageSender
    timestamp: str | None = None
    content: str | None = None
    agent_data: AgentMessageData | None = Field(default=None, alias="agentData")
    prompt_data: ActionPromptData | None = Field(default=None, alias="promptData")
    attachments: list[AttachmentMeta] | None = None


class AttachmentUploadResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    attachment_id: str = Field(alias="attachmentId")
    file_name: str = Field(alias="fileName")
    mime_type: str = Field(alias="mimeType")
    size_bytes: int = Field(alias="sizeBytes")


class StartRunResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run_id: str = Field(alias="runId")
    user_message_id: str = Field(alias="userMessageId")


class Channel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    title: str
    icon: str
    category: str | None = None


class CreateChannelRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str
    icon: str | None = None


class PostMessageRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: Literal["text", "action"]
    content: str | None = None
    action_id: str | None = Field(default=None, alias="actionId")
    label: str | None = None
    reply_to_message_id: str | None = Field(
        default=None, alias="replyToMessageId"
    )
    attachment_ids: list[str] | None = Field(default=None, alias="attachmentIds")

    @model_validator(mode="after")
    def validate_request(self) -> PostMessageRequest:
        if self.type == "action":
            if not self.action_id or not self.label:
                raise ValueError("actionId and label are required for type action")
        return self
