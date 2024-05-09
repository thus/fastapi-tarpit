import logging
from typing import Optional


class TarpitConfig():
    def __init__(
            self: "TarpitConfig",
            interval: int = 2,
            chunk_length_min: int = 1,
            chunk_length_max: int = 5,
            logger: Optional[logging.Logger] = None
    ) -> None:
        self.interval: int = interval
        self.chunk_length_min: int = chunk_length_min
        self.chunk_length_max: int = chunk_length_max
        self.logger = logger if logger else logging.getLogger(__name__)
