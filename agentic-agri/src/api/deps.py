"""FastAPI dependency wiring — in-memory or Postgres chat persistence."""

from __future__ import annotations

from dataclasses import dataclass

from chat.adapters.supervisor_stream import SupervisorStreamAdapter
from chat.repositories.attachment_repository import (
    AttachmentRepository,
    InMemoryAttachmentRepository,
    PostgresAttachmentRepository,
)
from chat.repositories.channel_member_repository import (
    ChannelMemberRepository,
    InMemoryChannelMemberRepository,
    PostgresChannelMemberRepository,
)
from chat.repositories.channel_repository import (
    ChannelRepository,
    InMemoryChannelRepository,
)
from chat.repositories.message_repository import (
    InMemoryMessageRepository,
    MessageRepository,
)
from chat.repositories.postgres_channel_repository import PostgresChannelRepository
from chat.repositories.postgres_message_repository import PostgresMessageRepository
from chat.repositories.run_event_repository import (
    PostgresRunEventRepository,
    RunEventRepository,
)
from chat.repositories.run_repository import PostgresRunRepository, RunRepository
from chat.repositories.thread_repository import (
    PostgresThreadRepository,
    ThreadRepository,
)
from chat.services.attachment_service import AttachmentService
from chat.services.channel_access_service import ChannelAccessService
from chat.services.channel_service import ChannelService
from chat.services.message_service import MessageService
from chat.services.post_message_validator import PostMessageValidator
from chat.services.run_service import RunService
from chat.settings import get_chat_settings

_active_runs: dict[str, str] = {}
_container: ChatContainer | None = None


@dataclass
class ChatContainer:
    channel_repository: ChannelRepository
    message_repository: MessageRepository
    channel_service: ChannelService
    message_service: MessageService
    run_service: RunService
    post_message_validator: PostMessageValidator
    channel_access: ChannelAccessService
    attachment_service: AttachmentService
    thread_repository: ThreadRepository | None = None
    run_repository: RunRepository | None = None
    run_event_repository: RunEventRepository | None = None


def create_chat_container(
    graph_app: object | None = None,
    active_runs: dict[str, str] | None = None,
    *,
    force_memory: bool = False,
) -> ChatContainer:
    settings = get_chat_settings()
    use_postgres = settings.use_postgres and not force_memory

    thread_repository: ThreadRepository | None = None
    run_repository: RunRepository | None = None
    run_event_repository: RunEventRepository | None = None
    attachment_repository: AttachmentRepository

    if use_postgres:
        thread_repository = PostgresThreadRepository()
        run_repository = PostgresRunRepository()
        run_event_repository = PostgresRunEventRepository()
        channel_repository: ChannelRepository = PostgresChannelRepository()
        member_repository: ChannelMemberRepository = PostgresChannelMemberRepository()
        message_repository: MessageRepository = PostgresMessageRepository(
            thread_repository=thread_repository
        )
        attachment_repository = PostgresAttachmentRepository()
        runs = {}
    else:
        channel_repository = InMemoryChannelRepository()
        member_repository = InMemoryChannelMemberRepository()
        message_repository = InMemoryMessageRepository(
            channel_repository=channel_repository
        )
        attachment_repository = InMemoryAttachmentRepository()
        runs = active_runs if active_runs is not None else _active_runs

    channel_access = ChannelAccessService(
        channel_repository,
        member_repository,
        chat_settings=settings,
    )
    post_message_validator = PostMessageValidator(message_repository)
    attachment_service = AttachmentService(
        attachment_repository,
        channel_access,
        chat_settings=settings,
    )

    stream_adapter = SupervisorStreamAdapter(graph_app=graph_app)

    return ChatContainer(
        channel_repository=channel_repository,
        message_repository=message_repository,
        channel_service=ChannelService(
            channel_repository,
            member_repository,
            channel_access=channel_access,
        ),
        message_service=MessageService(
            message_repository, channel_access, attachment_service
        ),
        post_message_validator=post_message_validator,
        channel_access=channel_access,
        attachment_service=attachment_service,
        run_service=RunService(
            message_repository=message_repository,
            channel_repository=channel_repository,
            stream_adapter=stream_adapter,
            active_runs=runs,
            thread_repository=thread_repository,
            run_repository=run_repository,
            run_event_repository=run_event_repository,
            chat_settings=settings,
            channel_access=channel_access,
            post_message_validator=post_message_validator,
            attachment_service=attachment_service,
        ),
        thread_repository=thread_repository,
        run_repository=run_repository,
        run_event_repository=run_event_repository,
    )


def get_chat_container() -> ChatContainer:
    global _container
    if _container is None:
        _container = create_chat_container()
    return _container


def set_chat_container(container: ChatContainer) -> None:
    global _container
    _container = container


def reset_chat_container() -> None:
    """Clear singleton and active runs — for tests."""
    global _container
    _container = None
    _active_runs.clear()
