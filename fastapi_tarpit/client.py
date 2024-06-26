import json
from asyncio import sleep
from datetime import datetime, timedelta
from enum import Enum
from random import randrange
from typing import List

from fastapi import Request
from starlette.datastructures import Address

from .config import TarpitConfig

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


class TarpitState(Enum):
    NEW = 1
    TRAPPED = 2
    CLOSED = 3


class TarpitClient:
    def __init__(self: "TarpitClient", request: Request,
                 config: TarpitConfig) -> None:
        if isinstance(request.client, Address):
            self.client = f"{request.client.host}:{request.client.port}"
        else:
            self.client = "<undefined>"
        self.request = request
        self.config = config
        self.start_time = datetime.now()
        self.log_next = self.start_time + timedelta(seconds=log_interval[0])
        self.log_interval_idx = 0
        self.logging_enabled = True
        self.log(TarpitState.NEW)

    def log(self: "TarpitClient", state: TarpitState) -> None:
        duration = duration_pretty_string(datetime.now() - self.start_time)

        if self.config.log_as_json:
            data = {
                "client": self.client,
                "path": self.request.url.path,
                "duration": duration
            }

        match state:
            case TarpitState.NEW:
                if self.config.log_as_json:
                    data["state"] = "NEW"
                else:
                    msg = (f"'{self.client}' got stuck in the tarpit visiting "
                           f"'{self.request.url.path}'")
            case TarpitState.TRAPPED:
                if self.config.log_as_json:
                    data["state"] = "TRAPPED"
                else:
                    msg = (f"'{self.client}' is still stuck in the tarpit "
                           f"after {duration} visiting "
                           f"'{self.request.url.path}'")
            case TarpitState.CLOSED:
                if self.config.log_as_json:
                    data["state"] = "CLOSED"
                else:
                    msg = (f"Trapped '{self.client} in the tarpit for "
                           f"{duration} visiting '{self.request.url.path}'")

        if self.config.log_as_json:
            msg = json.dumps(data)

        self.config.logger.info(msg)

    def close(self: "TarpitClient") -> None:
        self.log(TarpitState.CLOSED)

    def tick(self: "TarpitClient") -> None:
        """Used to log how long a client has been stuck in the tarpit at
           different time intervals (minute, hour, day, etc)."""
        if not self.logging_enabled or datetime.now() < self.log_next:
            return

        self.log(TarpitState.TRAPPED)

        self.log_interval_idx += 1
        try:
            seconds = log_interval[self.log_interval_idx]
        except IndexError:
            # This is unlikely to ever happen, but if it does, then just
            # disable logging.
            self.logging_enabled = False
        self.log_next = self.start_time + timedelta(seconds=seconds)

    def generate_chunk(self: "TarpitClient") -> bytes:
        length = randrange(self.config.chunk_length_min,  # noqa: S311
                           self.config.chunk_length_max)
        return b'.' * length

    async def wait(self: "TarpitClient") -> None:
        wait = randrange(self.config.chunk_wait_min,  # noqa: S311
                         self.config.chunk_wait_max)
        await sleep(wait)
