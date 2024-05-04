import logging
from asyncio import sleep
from contextlib import contextmanager
from datetime import datetime, timedelta
from random import randrange
from signal import SIGINT, getsignal, signal
from types import FrameType
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

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


class TarpitConfig():
    def __init__(
            self,
            interval: int = 2,
            output_length_min: int = 1,
            output_length_max: int = 5,
            logger: Optional[logging.Logger] = None
    ):
        self.interval: int = interval
        self.output_length_min: int = output_length_min
        self.output_length_max: int = output_length_max
        self.logger = logger if logger else logging.getLogger(__name__)


class TarpitClient:
    def __init__(self, request: Request, config: TarpitConfig):
        if isinstance(request.client, Address):
            self.host = f"{request.client.host}:{request.client.port}"
        else:
            self.host = "<undefined>"
        self.request = request
        self.config = config
        self.start_time = datetime.now()
        self.log_next = self.start_time + timedelta(seconds=log_interval[0])
        self.log_interval_idx = 0
        self.logging_enabled = True
        self.config.logger.info(f"'{self.host}' got stuck in the tarpit "
                                f"visiting '{request.url.path}'")

    def close(self) -> None:
        duration = duration_pretty_string(datetime.now() - self.start_time)
        self.config.logger.info(f"Trapped '{self.host} in the tarpit for "
                                f"{duration} visiting "
                                f"'{self.request.url.path}'")

    def tick(self) -> None:
        """Used to log how long a host has been stuck in the tarpit at
           different time intervals (minute, hour, day, etc)."""
        if not self.logging_enabled or datetime.now() < self.log_next:
            return

        duration = duration_pretty_string(datetime.now() - self.start_time)
        self.config.logger.info(f"'{self.host}' is still stuck in the tarpit "
                                f"after {duration} visiting "
                                f"'{self.request.url.path}'")

        self.log_interval_idx += 1
        try:
            seconds = log_interval[self.log_interval_idx]
        except IndexError:
            # This is unlikely to ever happen, but if it does, then just
            # disable logging.
            self.logging_enabled = False
        self.log_next = self.start_time + timedelta(seconds=seconds)

    def generate_bytes(self) -> bytes:
        length = randrange(self.config.output_length_min,
                           self.config.output_length_max)
        return b'.' * length


@contextmanager
def tarpit_connection(request: Request,
                      config: TarpitConfig) -> Iterator[TarpitClient]:
    client = TarpitClient(request, config)
    try:
        yield client
    finally:
        client.close()


async def tarpit_stream(request: Request,
                        config: TarpitConfig) -> AsyncIterator[bytes]:
    with tarpit_connection(request, config) as client:
        while tarpit_running:
            await sleep(config.interval)
            client.tick()
            yield client.generate_bytes()


class HTTPTarpitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, **kwargs: Any):
        self.config: TarpitConfig = TarpitConfig(**kwargs)
        self.routes: Dict[str, int] = {}

        default_sigint_handler = getsignal(SIGINT)

        def tarpit_shutdown(signum: int, frame: Optional[FrameType]) -> None:
            global tarpit_running
            tarpit_running = False

            if default_sigint_handler:
                default_sigint_handler(signum, frame)  # type: ignore

        signal(SIGINT, tarpit_shutdown)

        super().__init__(app)

    def get_routes(self, app: FastAPI) -> None:
        for route in app.routes:
            self.routes[route.path] = 1  # type: ignore

    async def dispatch(self, request: Request,
                       call_next: RequestResponseEndpoint) -> Any:
        if not self.routes:
            self.get_routes(request.app)

        if request.url.path not in self.routes:
            return StreamingResponse(tarpit_stream(request, self.config))

        return await call_next(request)
