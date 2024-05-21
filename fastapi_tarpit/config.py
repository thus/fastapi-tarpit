import logging
from typing import Optional


class TarpitConfig():
    def __init__(
            self: "TarpitConfig",
            chunk_wait_min: int = 1,
            chunk_wait_max: int = 5,
            chunk_length_min: int = 1,
            chunk_length_max: int = 5,
            log_as_json: bool = False,
            logger: Optional[logging.Logger] = None
    ) -> None:
        self.chunk_wait_min: int = chunk_wait_min
        self.chunk_wait_max: int = chunk_wait_max
        self.chunk_length_min: int = chunk_length_min
        self.chunk_length_max: int = chunk_length_max
        self.log_as_json: bool = log_as_json
        self.logger = logger if logger else logging.getLogger(__name__)
