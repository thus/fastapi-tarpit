import logging
from asyncio import sleep
from datetime import datetime, timedelta
from signal import SIGINT, getsignal, signal
from types import FrameType
from typing import Any, AsyncIterator, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from starlette.datastructures import Address
from starlette.middleware.base import (BaseHTTPMiddleware,
                                       RequestResponseEndpoint)

tarpit_running: bool = True

log_interval: List[int] = [
    60,            # 1 minute
    60*5,          # 5 minutes
    60*30,         # 30 minutes
    60*60,         # 1 hour
    60*60*24,      # 1 day
    60*60*24*7,    # 7 days
    60*60*24*30,   # 30 days
    60*60*24*60,   # 60 days
    60*60*24*90,   # 90 days
    60*60*24*365,  # one year
]


def duration_pretty_string(duration: timedelta) -> str:
    seconds = duration.seconds
    duration_str = []
    days, seconds = divmod(seconds, 86400)
    if days:
        duration_str.append(f"{days} {'days' if days > 1 else 'day'}")
    hours, seconds = divmod(seconds, 3600)
    if hours:
        duration_str.append(f"{hours} {'hours' if hours > 1 else 'hour'}")
    minutes, seconds = divmod(seconds, 60)
    if minutes:
        duration_str.append(f"{minutes} "
                            f"{'minutes' if minutes > 1 else 'minute'}")
    if seconds or not duration_str:
        duration_str.append(f"{seconds} "
                            f"{'second' if seconds == 1 else 'seconds'}")
    return " ".join(duration_str)


class TarpitClient:
    def __init__(self, request: Request, logger: logging.Logger):
        if isinstance(request.client, Address):
            self._host = f"{request.client.host}:{request.client.port}"
        else:
            self._host = "<undefined>"
        self._request = request
        self._logger = logger
        self._start_time = datetime.now()
        self._log_next = self._start_time + timedelta(seconds=log_interval[0])
        self._log_interval_idx = 0
        self._logging_enabled = True
        self._logger.info(f"'{self._host}' got stuck in the tarpit visiting "
                          f"'{request.url.path}'")

    def __del__(self) -> None:
        duration = duration_pretty_string(datetime.now() - self._start_time)
        self._logger.info(f"Trapped '{self._host} in the tarpit for "
                          f"{duration}")

    def tick(self) -> None:
        """Used to log how long a host has been stuck in the tarpit at
           different time intervals (minute, hour, day, etc)."""
        if not self._logging_enabled or datetime.now() < self._log_next:
            return

        duration = duration_pretty_string(datetime.now() - self._start_time)
        self._logger.info(f"'{self._host}' is still stuck in the tarpit "
                          f"after {duration}")

        self._log_interval_idx += 1
        try:
            seconds = log_interval[self._log_interval_idx]
        except IndexError:
            # This is unlikely to ever happen, but if it does, then just
            # disable logging.
            self._logging_enabled = False
        self._log_next = self._start_time + timedelta(seconds=seconds)


async def tarpit_stream(client: TarpitClient,
                        interval: int) -> AsyncIterator[bytes]:
    while tarpit_running:
        await sleep(interval)
        client.tick()
        yield b"."


class HTTPTarpitMiddleware(BaseHTTPMiddleware):
    def __init__(
            self,
            app: FastAPI,
            *,
            interval: int = 2,
            logger: Optional[logging.Logger] = None
    ):
        self._interval: int = interval
        self._logger = logger if logger else logging.getLogger(__name__)
        self._routes: Dict[str, int] = {}

        default_sigint_handler = getsignal(SIGINT)

        def tarpit_shutdown(signum: int, frame: Optional[FrameType]) -> None:
            global tarpit_running
            tarpit_running = False

            if default_sigint_handler:
                default_sigint_handler(signum, frame)  # type: ignore

        signal(SIGINT, tarpit_shutdown)

        super().__init__(app)

    def _get_routes(self, app: FastAPI) -> None:
        for route in app.routes:
            self._routes[route.path] = 1  # type: ignore

    async def dispatch(self, request: Request,
                       call_next: RequestResponseEndpoint) -> Any:
        if not self._routes:
            self._get_routes(request.app)

        if request.url.path not in self._routes:
            client = TarpitClient(request, self._logger)
            return StreamingResponse(tarpit_stream(client, self._interval))

        return await call_next(request)
