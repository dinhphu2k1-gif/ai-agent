"""Attachment metadata and local file storage (P0)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from chat.db import transaction


@dataclass(frozen=True)
class AttachmentRecord:
    id: UUID
    channel_id: str
    thread_id: UUID | None
    uploader_id: str
    file_name: str
    mime_type: str
    size_bytes: int
    storage_path: str


class AttachmentRepository(ABC):
    @abstractmethod
    def create(
        self,
        channel_id: str,
        uploader_id: str,
        file_name: str,
        mime_type: str,
        size_bytes: int,
        storage_path: str,
        *,
        thread_id: UUID | None = None,
        attachment_id: UUID | None = None,
    ) -> AttachmentRecord:
        """Persist attachment metadata."""

    @abstractmethod
    def get_by_id(self, attachment_id: UUID) -> AttachmentRecord | None:
        """Load attachment by id."""

    @abstractmethod
    def list_for_channel_user(
        self, channel_id: str, uploader_id: str, attachment_ids: list[UUID]
    ) -> list[AttachmentRecord]:
        """Return attachments owned by user in channel (subset of ids)."""

    @abstractmethod
    def link_to_message(self, message_id: UUID, attachment_ids: list[UUID]) -> None:
        """Associate attachments with a message."""


class InMemoryAttachmentRepository(AttachmentRepository):
    def __init__(self) -> None:
        self._by_id: dict[UUID, AttachmentRecord] = {}
        self._message_links: dict[UUID, list[UUID]] = {}

    def create(
        self,
        channel_id: str,
        uploader_id: str,
        file_name: str,
        mime_type: str,
        size_bytes: int,
        storage_path: str,
        *,
        thread_id: UUID | None = None,
        attachment_id: UUID | None = None,
    ) -> AttachmentRecord:
        att_id = attachment_id or uuid4()
        record = AttachmentRecord(
            id=att_id,
            channel_id=channel_id,
            thread_id=thread_id,
            uploader_id=uploader_id,
            file_name=file_name,
            mime_type=mime_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
        )
        self._by_id[att_id] = record
        return record

    def get_by_id(self, attachment_id: UUID) -> AttachmentRecord | None:
        return self._by_id.get(attachment_id)

    def list_for_channel_user(
        self, channel_id: str, uploader_id: str, attachment_ids: list[UUID]
    ) -> list[AttachmentRecord]:
        out: list[AttachmentRecord] = []
        for att_id in attachment_ids:
            record = self._by_id.get(att_id)
            if (
                record
                and record.channel_id == channel_id
                and record.uploader_id == uploader_id
            ):
                out.append(record)
        return out

    def link_to_message(self, message_id: UUID, attachment_ids: list[UUID]) -> None:
        self._message_links[message_id] = list(attachment_ids)

    def get_for_message(self, message_id: UUID) -> list[AttachmentRecord]:
        return [
            self._by_id[att_id]
            for att_id in self._message_links.get(message_id, [])
            if att_id in self._by_id
        ]


class PostgresAttachmentRepository(AttachmentRepository):
    def create(
        self,
        channel_id: str,
        uploader_id: str,
        file_name: str,
        mime_type: str,
        size_bytes: int,
        storage_path: str,
        *,
        thread_id: UUID | None = None,
        attachment_id: UUID | None = None,
    ) -> AttachmentRecord:
        att_id = attachment_id or uuid4()
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat.chat_attachments (
                        id, channel_id, thread_id, uploader_id,
                        file_name, mime_type, size_bytes, storage_path
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, channel_id, thread_id, uploader_id,
                              file_name, mime_type, size_bytes, storage_path
                    """,
                    (
                        str(att_id),
                        channel_id,
                        str(thread_id) if thread_id else None,
                        uploader_id,
                        file_name,
                        mime_type,
                        size_bytes,
                        storage_path,
                    ),
                )
                row = cur.fetchone()
        return _row_to_attachment(row)

    def get_by_id(self, attachment_id: UUID) -> AttachmentRecord | None:
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, channel_id, thread_id, uploader_id,
                           file_name, mime_type, size_bytes, storage_path
                    FROM chat.chat_attachments WHERE id = %s
                    """,
                    (str(attachment_id),),
                )
                row = cur.fetchone()
        if not row:
            return None
        return _row_to_attachment(row)

    def list_for_channel_user(
        self, channel_id: str, uploader_id: str, attachment_ids: list[UUID]
    ) -> list[AttachmentRecord]:
        if not attachment_ids:
            return []
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, channel_id, thread_id, uploader_id,
                           file_name, mime_type, size_bytes, storage_path
                    FROM chat.chat_attachments
                    WHERE channel_id = %s AND uploader_id = %s
                      AND id = ANY(%s::uuid[])
                    """,
                    (
                        channel_id,
                        uploader_id,
                        [str(aid) for aid in attachment_ids],
                    ),
                )
                rows = cur.fetchall()
        return [_row_to_attachment(row) for row in rows]

    def link_to_message(self, message_id: UUID, attachment_ids: list[UUID]) -> None:
        if not attachment_ids:
            return
        with transaction() as conn:
            with conn.cursor() as cur:
                for att_id in attachment_ids:
                    cur.execute(
                        """
                        INSERT INTO chat.chat_message_attachments (message_id, attachment_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (str(message_id), str(att_id)),
                    )


def _row_to_attachment(row: tuple) -> AttachmentRecord:
    return AttachmentRecord(
        id=row[0],
        channel_id=row[1],
        thread_id=row[2],
        uploader_id=row[3],
        file_name=row[4],
        mime_type=row[5],
        size_bytes=int(row[6]),
        storage_path=row[7],
    )
