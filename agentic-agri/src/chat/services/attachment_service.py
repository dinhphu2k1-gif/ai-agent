"""Upload and validate chat attachments (local storage P0)."""

from __future__ import annotations

import re
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile

from api.errors import ValidationFailedError
from api.schemas.chat import AttachmentMeta, AttachmentUploadResponse
from chat.repositories.attachment_repository import AttachmentRepository
from chat.services.channel_access_service import ChannelAccessService
from chat.settings import ChatSettings, get_chat_settings

_MAX_BYTES = 10 * 1024 * 1024
_SAFE_NAME = re.compile(r"[^a-zA-Z0-9._-]+")


class AttachmentService:
    def __init__(
        self,
        attachment_repository: AttachmentRepository,
        channel_access: ChannelAccessService,
        chat_settings: ChatSettings | None = None,
    ) -> None:
        self._attachments = attachment_repository
        self._channel_access = channel_access
        self._settings = chat_settings or get_chat_settings()

    def _storage_root(self) -> Path:
        root = Path(self._settings.attachment_storage_path)
        root.mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        base = Path(name).name or "upload.bin"
        return _SAFE_NAME.sub("_", base)[:200]

    async def upload(
        self,
        channel_id: str,
        user_id: str,
        upload: UploadFile,
    ) -> AttachmentUploadResponse:
        self._channel_access.authorize_participant(channel_id, user_id)

        file_name = self._sanitize_filename(upload.filename or "upload.bin")
        mime_type = (upload.content_type or "application/octet-stream").strip()
        data = await upload.read()
        size_bytes = len(data)
        if size_bytes == 0:
            raise ValidationFailedError("Uploaded file is empty")
        if size_bytes > _MAX_BYTES:
            raise ValidationFailedError(
                f"File exceeds maximum size of {_MAX_BYTES} bytes"
            )

        attachment_id = uuid4()
        dest_dir = self._storage_root() / channel_id / str(attachment_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / file_name
        dest_path.write_bytes(data)
        storage_path = str(dest_path)

        record = self._attachments.create(
            channel_id,
            user_id,
            file_name,
            mime_type,
            size_bytes,
            storage_path,
            attachment_id=attachment_id,
        )
        return AttachmentUploadResponse(
            attachment_id=str(record.id),
            file_name=record.file_name,
            mime_type=record.mime_type,
            size_bytes=record.size_bytes,
        )

    def resolve_for_message(
        self,
        channel_id: str,
        user_id: str,
        attachment_ids: list[str] | None,
    ) -> list[AttachmentMeta]:
        if not attachment_ids:
            return []
        uuids: list[UUID] = []
        for raw in attachment_ids:
            try:
                uuids.append(UUID(str(raw)))
            except ValueError as exc:
                raise ValidationFailedError(f"Invalid attachment id: {raw}") from exc

        records = self._attachments.list_for_channel_user(
            channel_id, user_id, uuids
        )
        if len(records) != len(uuids):
            raise ValidationFailedError(
                "One or more attachments are missing or not owned by this user"
            )
        return [
            AttachmentMeta(
                id=str(record.id),
                file_name=record.file_name,
                mime_type=record.mime_type,
                size_bytes=record.size_bytes,
            )
            for record in records
        ]

    def link_to_message(
        self,
        message_id: UUID,
        attachment_ids: list[str] | None,
        channel_id: str,
        user_id: str,
    ) -> None:
        if not attachment_ids:
            return
        uuids = [UUID(str(aid)) for aid in attachment_ids]
        records = self._attachments.list_for_channel_user(
            channel_id, user_id, uuids
        )
        if len(records) != len(uuids):
            raise ValidationFailedError("Invalid attachmentIds for this channel")
        self._attachments.link_to_message(message_id, uuids)

    def metadata_for_message(self, message_id: str) -> list[AttachmentMeta]:
        if not hasattr(self._attachments, "get_for_message"):
            return []
        try:
            message_uuid = UUID(message_id)
        except ValueError:
            return []
        records = self._attachments.get_for_message(message_uuid)
        return [
            AttachmentMeta(
                id=str(record.id),
                file_name=record.file_name,
                mime_type=record.mime_type,
                size_bytes=record.size_bytes,
            )
            for record in records
        ]
