from asyncio import sleep
from contextlib import contextmanager
from signal import SIGINT, getsignal, signal
from types import FrameType
from typing import Any, AsyncIterator, Dict, Iterator, Optional

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from starlette.middleware.base import (BaseHTTPMiddleware,
                                       RequestResponseEndpoint)

from .client import TarpitClient
from .config import TarpitConfig

tarpit_running: bool = True


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
    def __init__(self: "HTTPTarpitMiddleware", app: FastAPI,
                 **kwargs: Any) -> None:
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

    def get_routes(self: "HTTPTarpitMiddleware", app: FastAPI) -> None:
        for route in app.routes:
            self.routes[route.path] = 1  # type: ignore

    async def dispatch(self: "HTTPTarpitMiddleware", request: Request,
                       call_next: RequestResponseEndpoint) -> Any:
        if not self.routes:
            self.get_routes(request.app)

        if request.url.path not in self.routes:
            return StreamingResponse(tarpit_stream(request, self.config))

        return await call_next(request)
