import asyncio
import threading
from contextlib import suppress
from collections.abc import Callable
from dataclasses import dataclass

from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, ConnectEvent, DisconnectEvent


VoteCallback = Callable[[str, str], None]
CommentCallback = Callable[[str, str], None]
StatusCallback = Callable[[str], None]


@dataclass
class LiveComment:
    username: str
    comment: str


class TikTokModule:

    def __init__(
        self,
        username: str,
        on_vote: VoteCallback | None = None,
        on_comment: CommentCallback | None = None,
        on_status: StatusCallback | None = None,
    ) -> None:

        self.username = username
        self.on_vote = on_vote
        self.on_comment = on_comment
        self.on_status = on_status
        self.thread: threading.Thread | None = None
        self.connected = False

        self.client = TikTokLiveClient(
            unique_id=username
        )

        @self.client.on(ConnectEvent)
        async def on_connect(_: ConnectEvent):
            self.connected = True
            self._status(f"Connected to @{self.username}")

        @self.client.on(DisconnectEvent)
        async def on_disconnect(_: DisconnectEvent):
            self.connected = False
            self._status(f"Disconnected from @{self.username}")

        @self.client.on(CommentEvent)
        async def on_comment(event: CommentEvent):
            username = event.user.nickname or event.user.unique_id
            comment = event.comment.strip()

            if self.on_comment:
                self.on_comment(username, comment)

            if self._is_vote(comment) and self.on_vote:
                self.on_vote(username, comment[0].upper())

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return

        self.thread = threading.Thread(
            target=self._run,
            daemon=True
        )
        self.thread.start()

    def stop(self) -> None:
        coroutine = self.client.disconnect(close_client=True)
        loop = getattr(self.client, "_asyncio_loop", None)
        try:
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(coroutine, loop)
            else:
                asyncio.run(coroutine)
        except Exception:
            with suppress(RuntimeError):
                coroutine.close()
        self.connected = False
        self._status("Nincs kapcsolat")

    def _run(self) -> None:
        self._status(f"Kapcsolódás @{self.username}...")
        try:
            self.client.run()
        except Exception as exc:
            self.connected = False
            self._status(f"TikTok Live error: {exc}")

    def _status(self, message: str) -> None:
        if self.on_status:
            self.on_status(message)

    def _is_vote(self, comment: str) -> bool:
        value = comment.strip().upper()
        return value in {"A", "B", "C", "D"}
